import torch
from sqlalchemy.orm import Session, aliased
from torch.utils.data import DataLoader, Dataset, random_split

import app.utils.database as db


class SaltybetDataset(Dataset):
    def __init__(self):
        # Get the Data from the Database
        with Session(db.engine) as session:
            red = aliased(db.Character)
            blue = aliased(db.Character)

            match_data = session.query(
                red.id,
                blue.id,
                db.Match.winner
            ).where(
                db.Match.red == red.name
            ).where(
                db.Match.blue == blue.name
            ).all()

            self.vocab = {name: _id for _id, name in session.query(db.Character.id, db.Character.name).all()}

        self.x, self.y = [], []
        for r, b, w in match_data:
            self.x.append([r, b])
            self.y.append([1, 0] if w == 'red' else [0, 1])
        self.x = torch.LongTensor(self.x)
        self.y = torch.Tensor(self.y)

        del match_data, red, blue

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        return self.x[idx], self.y[idx]


dataset = SaltybetDataset()
vocab = dataset.vocab
num_characters = len(vocab)

train, val, test = random_split(dataset, [0.7, 0.1, 0.2], torch.Generator().manual_seed(42))

batch_size = 2 ** 10
production_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
train_loader = DataLoader(train, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val, batch_size=batch_size)
test_loader = DataLoader(test, batch_size=batch_size)

del dataset
