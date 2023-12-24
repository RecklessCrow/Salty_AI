from datetime import datetime

import pytz
from tqdm import tqdm

from models.transformer_model import OutcomePredictor
from models.utils import *

logging.basicConfig(level=logging.INFO)

# Define your device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# device = torch.device("cpu")

# Define your model
model = OutcomePredictor(num_tokens=db.get_num_tokens() + 1).to(device)
# model = CharacterGNN(num_nodes=db.get_num_tokens() + 1, embedding_dim=1024, hidden_dim=512, num_classes=2).to(device)
loss_fn = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)

# Learning rate scheduler
scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)

validate = True
batch_size = 2 ** 14
train_percentage = 0.8
epochs = 6

if validate:
    dataloader_train, dataloader_validation = load_data(batch_size=batch_size, train_percentage=train_percentage)

    # Iterate over your DataLoader
    for epoch in range(epochs):
        pb = tqdm(dataloader_train, desc=f"Epoch {epoch + 1}", total=len(dataloader_train))
        training_epoch(pb, model, loss_fn, optimizer, device)

        # Validation
        validation_epoch(dataloader_validation, model, loss_fn, device)

        # Update learning rate scheduler
        # scheduler.step()

else:
    dataloader = load_data(batch_size=batch_size, train_percentage=1, split=False)

    # Iterate over your DataLoader
    for epoch in range(epochs):
        pb = tqdm(dataloader, desc=f"Epoch {epoch + 1}", total=len(dataloader))
        training_epoch(pb, model, loss_fn, optimizer, device)

        # Update learning rate scheduler
        # scheduler.step()

# Save your model
tz = pytz.timezone('America/New_York')
dt = datetime.now(tz=tz).strftime("%Y-%m-%d-%H-%M-%S")
model.save_model(f"/models/{dt}.onnx")
