import logging
import os

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from database.interface import db
from models.data import MatchDataset


def load_data(batch_size, train_percentage=0.8, workers=0):
    data_file = "/data/matches.csv"
    if not os.path.exists(data_file):
        existing_matchups = {}
        with open(data_file, "w") as f:
            matchups = db.get_training_data()
            for red, blu, (r_win, b_win) in tqdm(matchups, desc="Loading data"):
                if (red, blu) in existing_matchups:
                    existing_matchups[red, blu][0] += r_win
                    existing_matchups[red, blu][1] += b_win
                elif (blu, red) in existing_matchups:
                    existing_matchups[blu, red][0] += b_win
                    existing_matchups[blu, red][1] += r_win
                else:
                    existing_matchups[red, blu] = [r_win, b_win]

            for (red, blu), (red_count, blu_count) in tqdm(existing_matchups.items(), desc="Calculating winrates"):
                red_winrate = red_count / (red_count + blu_count)
                blu_winrate = blu_count / (red_count + blu_count)
                f.write(f"{red},{blu},{red_winrate},{blu_winrate}\n")

    with open(data_file, "r") as f:
        x = []
        y = []
        for line in tqdm(f, desc="Loading data"):
            red, blu, red_winrate, blu_winrate = line.strip().split(",")
            red = int(red)
            blu = int(blu)
            red_winrate = float(red_winrate)
            blu_winrate = float(blu_winrate)
            _x = (red, blu)
            _y = (red_winrate, blu_winrate)
            x.append(_x)
            y.append(_y)

    dataset = MatchDataset(x, y)

    if train_percentage in [0.0, 1.0]:
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True,
            num_workers=workers
        ), None

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
        shuffle=True,
        num_workers=workers
    )

    dataloader_validation = DataLoader(
        dataset_validation,
        batch_size=batch_size,
        num_workers=workers
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

    return val_accuracy, val_loss / len(dataloader_validation)
