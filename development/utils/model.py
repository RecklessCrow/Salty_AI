from datetime import datetime

import torch
from torch.nn import (
    Module,
    Embedding,
    Sequential,
    Linear,
    Flatten,
)

time_stamp = datetime.now().strftime('%m-%d_%H-%M-%S')


class BetBot(Module):
    def __init__(self, num_characters, *args, **kwargs):
        super().__init__(*args, **kwargs)

        e_dim = 1024

        self.embeddings = Embedding(
            num_embeddings=num_characters + 1,
            embedding_dim=e_dim,
        )

        # self.transformer = TransformerEncoder(
        #     encoder_layer=TransformerEncoderLayer(
        #         d_model=e_dim,
        #         nhead=16,
        #     ),
        #     num_layers=12,
        # )

        self.logits = Sequential(
            Flatten(),
            Linear(e_dim * 2, 1),
            # Sigmoid()
        )

    def forward(self, x):
        x = self.embeddings(x)
        # x = self.transformer(x)
        x = self.logits(x)
        return x
