import logging

import torch
from torch.utils.data import DataLoader

from database.driver import db
from models.data import MatchDataset


def load_data(batch_size, train_percentage=0.8, split=True):
    # Get data
    matches = db.get_training_data()
    dataset = MatchDataset(matches)

    if not split:
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True
        )

    # Split data
    train_size = int(len(dataset) * train_percentage)
    validation_size = len(dataset) - train_size
    dataset_train, dataset_validation = torch.utils.data.random_split(
        dataset,
        [train_size, validation_size]
    )

    # Define DataLoaders
    dataloader_train = DataLoader(
        dataset_train,
        batch_size=batch_size,
        shuffle=True
    )

    dataloader_validation = DataLoader(
        dataset_validation,
        batch_size=batch_size
    )

    return dataloader_train, dataloader_validation


def training_epoch(pb, model, loss_fn, optimizer, device):
    model.train()
    num_matches = 0
    num_correct = 0
    total_loss = 0
    for x, y in pb:
        x, y = x.to(device), y.to(device)

        # Forward pass
        logits = model(x)
        loss = loss_fn(logits, y)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # Calculate running accuracy
        num_matches += len(y)
        num_correct += (logits.argmax(dim=1) == y.argmax(dim=1)).sum().item()
        total_loss += loss.item()

        # Log metrics
        pb.set_postfix(
            loss=total_loss / len(pb),
            accuracy=num_correct / num_matches
        )


def validation_epoch(dataloader_validation, model, loss_fn, device):
    model.eval()
    val_loss = 0
    num_val_matches = 0
    num_val_correct = 0
    with torch.no_grad():
        for x, y in dataloader_validation:
            x, y = x.to(device), y.to(device)

            # Forward pass for validation
            logits = model(x)
            loss = loss_fn(logits, y)

            # Calculate running accuracy and total loss for validation
            num_val_matches += len(y)
            num_val_correct += (logits.argmax(dim=1) == y.argmax(dim=1)).sum().item()
            val_loss += loss.item()

    val_accuracy = num_val_correct / num_val_matches
    logging.info(f"Validation Accuracy: {val_accuracy}, "
                 f"Validation Loss: {val_loss / len(dataloader_validation)}")
