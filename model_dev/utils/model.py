from datetime import datetime

from torch.nn import (
    Module,
    Embedding,
    Sequential,
    Flatten,
)

import torchbnn as bnn

time_stamp = datetime.now().strftime('%m-%d_%H-%M-%S')


class BetBot(Module):
    def __init__(self, num_characters, *args, **kwargs):
        super().__init__(*args, **kwargs)

        e_dim = 1024

        self.embeddings = Embedding(
            num_embeddings=num_characters + 1,
            embedding_dim=e_dim,
        )

        # Set up a bayesian network for the logits
        self.logits = Sequential(
            Flatten(),
            bnn.BayesLinear(
                in_features=e_dim * 2,
                out_features=2,
                prior_mu=0,
                prior_sigma=0.1,
            ),
        )

    def forward(self, x):
        x = self.embeddings(x)
        x = self.logits(x)
        return x
