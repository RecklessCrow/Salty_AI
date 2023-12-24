from random import random
from typing import List

import torch
from torch.utils.data import Dataset

from database.models import MatchUp


class MatchDataset(Dataset):
    def __init__(self, match_info: List[MatchUp]):
        self.data = []
        self.labels = []

        for red, blue, winner in match_info:
            x = torch.tensor([red, blue], dtype=torch.long)
            y = torch.tensor(winner, dtype=torch.float32)

            self.data.append(x)
            self.labels.append(y)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):

        data = self.data[index]
        label = self.labels[index]

        if isinstance(index, slice):
            # Randomly choose which indices to flip
            data = [x.flip(0) if random() > 0.5 else x for x in data]
            label = [y.flip(0) if random() > 0.5 else y for y in label]
        else:
            if random() > 0.5:
                data = data.flip(0)
                label = label.flip(0)

        return self.transform(data), label

    def transform(self, data):
        # Add any additional transformations if needed
        return data
