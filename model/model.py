import os
from datetime import datetime

import torch
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from torch.nn import (
    Module,
    Embedding,
    Sequential,
    Linear,
    Flatten
)

time_stamp = datetime.now().strftime('%m-%d_%H-%M-%S')


class BetBot(Module):
    def __init__(self, num_characters, *args, **kwargs):
        super().__init__(*args, **kwargs)

        e_dim = 512

        self.embeddings = Embedding(
            num_embeddings=num_characters,
            embedding_dim=512,
        )

        self.logits = Sequential(
            Flatten(),
            Linear(e_dim*2, 1)
        )

    def forward(self, x):
        x = self.embeddings(x)
        x = self.logits(x)
        return x


if __name__ == '__main__':
    from sqlalchemy.orm import aliased, Session
    import app.utils.database as db
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

        num_characters = len(session.query(db.Character.id).all())

    inputs = torch.LongTensor([[r, b] for r, b, w in match_data])

    model = BetBot(num_characters)
    print(model(inputs[:32]))
