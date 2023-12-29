from datetime import datetime

import pytz

from models.networks.simple import Simple
from models.utils import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TrainingLoop")

# Define device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# device = torch.device("cpu")
logger.info(f"Using device {device}")

# Variables
label_smoothing = 0
learning_rate = 0.0001

epochs = 30
batch_size = 2 ** 14
train_percentage = 0.0

# Load the data
dataloader_train, dataloader_validation = load_data(
    batch_size=batch_size,
    train_percentage=train_percentage,
    workers=8
)

# Define loss function
loss_fn = torch.nn.CrossEntropyLoss(label_smoothing=label_smoothing)

best_results = {}
model = Simple(
    num_tokens=db.get_num_tokens(),
    num_classes=2,
    e_dim=1024,
    dropout=0.1,
).to(device)
key = str(model)
best_results[key] = {"loss": float("inf")}
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

# Iterate over your DataLoader
for epoch in range(epochs):
    pb = tqdm(dataloader_train, desc=f"Epoch {epoch + 1}", total=len(dataloader_train))
    training_epoch(pb, model, loss_fn, optimizer, device)

    # Validation
    if train_percentage > 0:
        val_acc, val_loss = validation_epoch(dataloader_validation, model, loss_fn, device)

        if best_results[key]["loss"] > val_loss:
            best_results[key]["loss"] = val_loss
            best_results[key]["acc"] = val_acc
            best_results[key]["epoch"] = epoch + 1
            logger.info(f"New best results for {key}: {val_acc:.4f} accuracy, {val_loss:.4f} loss, {epoch + 1} epochs")

if train_percentage > 0:
    logger.info("Best results:")
    for model_name, result in best_results.items():
        logger.info(f"{model_name}: {result['acc']:.4f} accuracy, {result['loss']:.4f} loss, {result['epoch']} epochs")

# Save your model
tz = pytz.timezone('America/New_York')
dt = datetime.now(tz=tz).strftime("%Y-%m-%d-%H-%M-%S")
model.save_model(f"/models/{model}-{dt}.onnx")
logger.info(f"Saved model to /models/{model}-{dt}.onnx")
