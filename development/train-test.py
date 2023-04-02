import gc

import numpy as np
import torch
from torch.nn import BCEWithLogitsLoss
from torch.optim import AdamW
from tqdm import tqdm

from utils.data import train_loader, num_characters, val_loader
from utils.model import BetBot

device = "cuda"


def main():
    torch.manual_seed(42)
    model = BetBot(num_characters).to(device)
    optimizer = AdamW(model.parameters())
    loss_fn = BCEWithLogitsLoss()
    scaler = torch.cuda.amp.GradScaler()
    num_accumulation_steps = 4

    for epoch in range(100):
        losses = []
        correct = 0
        count = 0

        model.train()
        with tqdm(train_loader, unit="batch") as tepoch:
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
                if ((idx + 1) % num_accumulation_steps == 0) or (idx + 1 == len(train_loader)):
                    scaler.step(optimizer)
                    scaler.update()
                    optimizer.zero_grad()

                # Garbage Collection
                torch.cuda.empty_cache()
                _ = gc.collect()

                correct += (torch.round(torch.sigmoid(outputs)) == labels).sum().item()
                count += len(labels)
                tepoch.set_postfix(
                    loss=np.mean(losses),
                    accuracy=f"{correct / count:.2%}",
                )

                if idx + 1 == len(train_loader):
                    train_loss = np.mean(losses)
                    train_acc = correct / count
                    val_losses = []
                    val_correct = 0
                    val_count = 0

                    model.eval()
                    for idx, (inputs, labels) in enumerate(val_loader):
                        inputs, labels = inputs.to(device), labels.to(device)
                        outputs = model(inputs)
                        with torch.no_grad():
                            loss = loss_fn(outputs, labels)
                        val_losses.append(loss.item())

                        val_correct += (torch.round(torch.sigmoid(outputs)) == labels).sum().item()
                        val_count += len(labels)

                        tepoch.set_postfix(
                            loss=train_loss,
                            accuracy=f"{train_acc:.2%}",
                            val_loss=np.mean(val_losses),
                            val_accuracy=f"{val_correct / val_count:.2%}",
                        )


if __name__ == '__main__':
    main()
