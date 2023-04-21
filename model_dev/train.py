import gc
import json
import os
import time

import numpy as np
import torch
from torch.nn import CrossEntropyLoss
from torch.optim import AdamW
from tqdm import tqdm

from utils.data import production_loader, num_characters
from utils.model import BetBot

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")


def main():
    model = BetBot(num_characters).to(device)
    optimizer = AdamW(model.parameters())
    loss_fn = CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler()
    num_accumulation_steps = 4

    epochs = 5

    for epoch in range(epochs):
        losses = []
        correct = 0
        count = 0

        model.train()
        with tqdm(production_loader, unit="batch") as tepoch:
            tepoch.set_description(f"Epoch {epoch}")
            for idx, (inputs, labels) in enumerate(tepoch):
                inputs, labels = inputs.to(device), labels.to(device)

                # Automatic Tensor Casting
                with torch.cuda.amp.autocast():
                    outputs = model(inputs)
                    loss = loss_fn(outputs, labels)
                scaler.scale(loss).backward()  # Automatic Gradient Scaling

                # Normalize the Gradients
                loss = loss / num_accumulation_steps
                losses.append(loss.item())

                # Gradient Accumulation
                if ((idx + 1) % num_accumulation_steps == 0) or (idx + 1 == len(production_loader)):
                    scaler.step(optimizer)
                    scaler.update()
                    optimizer.zero_grad()

                # Garbage Collection
                torch.cuda.empty_cache()
                _ = gc.collect()

                # Calculate Accuracy
                count += inputs.shape[0]
                truth_mask = torch.argmax(outputs, dim=1) == torch.argmax(labels, dim=1)
                correct += torch.sum(truth_mask).item()

                tepoch.set_postfix(
                    loss=np.mean(losses),
                    accuracy=f"{correct / count:.2%}",
                )

    dir_name = time.strftime("%Y.%m.%d-%H.%M")
    os.makedirs(f"../models/{dir_name}")

    # Save the model
    file_name = f"../models/{dir_name}/model.onnx"
    torch.onnx.export(
        model.eval().cpu(),  # model being run
        torch.tensor([[0, 0]]),  # model input (or a tuple for multiple inputs)
        file_name,  # where to save the model
        export_params=True,  # store the trained parameter weights inside the model file
        do_constant_folding=True,  # whether to execute constant folding for optimization
        input_names=['input'],  # the model's input names
        output_names=['output'],  # the model's output names
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}  # variable length axes
    )

    # Save the "vocab" file for the characters the model was trained on
    file_name = f"../models/{dir_name}/vocab.json"
    with open(file_name, "w") as f:
        json.dump(production_loader.dataset.vocab, f)


if __name__ == '__main__':
    main()
