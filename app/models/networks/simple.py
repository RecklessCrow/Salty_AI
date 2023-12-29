from torch import nn

from models.networks.base import BaseModel
from blitz.modules import BayesianLinear


class Simple(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(e_mode=None, *args, **kwargs)

        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=self.e_dim,
                nhead=16,
                activation="gelu",
                batch_first=True
            ),
            num_layers=2
        )

        # self.fc1 = nn.Linear(
        #     in_features=self.e_dim * 2,
        #     out_features=self.e_dim
        # )
        #
        # self.fc2 = nn.Linear(
        #     in_features=self.e_dim,
        #     out_features=self.num_classes
        # )

        self.fc1 = BayesianLinear(
            in_features=self.e_dim * 2,
            out_features=self.e_dim
        )

        self.fc2 = BayesianLinear(
            in_features=self.e_dim,
            out_features=self.num_classes
        )

        self.activation = nn.GELU()

    def forward(self, x):
        x = self.embedding(x)
        x = self.transformer(x)

        if self.e_mode is None:
            x = x.flatten(start_dim=1)

        x = self.dropout(x)

        x = self.fc1(x)
        x = self.activation(x)
        x = self.fc2(x)

        return x

    def __str__(self):
        return f"SimpleShared"
