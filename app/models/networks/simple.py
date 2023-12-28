from torch import nn

from models.networks.base import BaseModel


class Simple(BaseModel):
    def __init__(self, *args, **kwargs):
        super().__init__(e_mode=None, *args, **kwargs)

        # self.transformer = nn.TransformerEncoder(
        #     nn.TransformerEncoderLayer(
        #         d_model=self.e_dim,
        #         nhead=16,
        #         activation="gelu",
        #         batch_first=True
        #     ),
        #     num_layers=2
        # )

        self.fc1 = nn.Linear(
            in_features=self.e_dim * 2,
            out_features=self.e_dim
        )

        self.fc2 = nn.Linear(
            in_features=self.e_dim,
            out_features=self.num_classes
        )

        # prior_mu = 0
        # prior_sigma = 0.01
        #
        # self.fc1 = BayesLinear(
        #     in_features=self.e_dim * 2,
        #     out_features=self.e_dim,
        #     prior_mu=prior_mu,
        #     prior_sigma=prior_sigma
        # )
        #
        # self.fc2 = BayesLinear(
        #     in_features=self.e_dim,
        #     out_features=self.num_classes,
        #     prior_mu=prior_mu,
        #     prior_sigma=prior_sigma
        # )

        self.activation = nn.GELU()

    def forward(self, x):
        x = self.embedding(x)
        # x = self.transformer(x)

        if self.e_mode is None:
            x = x.flatten(start_dim=1)

        x = self.dropout(x)

        x = self.fc1(x)
        x = self.activation(x)
        x = self.fc2(x)

        return x

    def __str__(self):
        return f"SimpleShared"
