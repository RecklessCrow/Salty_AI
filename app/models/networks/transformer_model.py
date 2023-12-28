import torch.nn as nn
import torch.onnx

from models.networks.bayesian import BayesianLinearLayer


class OutcomePredictor(nn.Module):
    def __init__(self, num_tokens, e_dim=512, dropout=0.5):
        super(OutcomePredictor, self).__init__()

        self.char_embedding = nn.Embedding(num_tokens, e_dim)
        self.char_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=e_dim,
                nhead=8,
                dropout=dropout,
                activation="gelu",
                batch_first=True
            ),
            num_layers=2
        )

        self.match_embedding = nn.Embedding(num_tokens, e_dim)
        self.match_transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=e_dim,
                nhead=8,
                dropout=dropout,
                activation="gelu",
                batch_first=True
            ),
            num_layers=2
        )
        self.match_fc = BayesianLinearLayer(e_dim, e_dim // 2)
        self.fc = BayesianLinearLayer(e_dim * 3, e_dim)
        self.logits = BayesianLinearLayer(e_dim, 2)

        # self.match_fc = nn.Linear(e_dim, e_dim // 2)
        # self.fc = nn.Linear(e_dim * 3, e_dim)
        # self.logits = nn.Linear(e_dim, 2)

        self.activation = nn.GELU()

        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # Character information
        red, blu = x[:, 0], x[:, 1]

        red = self.char_embedding(red)
        red = self.char_transformer(red)
        red = self.dropout(red)

        blu = self.char_embedding(blu)
        blu = self.char_transformer(blu)
        blu = self.dropout(blu)

        # Matchup information
        x = self.match_embedding(x)
        x = self.match_transformer(x)
        x = self.match_fc(x)
        x = self.activation(x)
        x = x.flatten(start_dim=1)
        x = self.dropout(x)

        # Combine and encode the information into a single vector
        x = torch.cat([red, blu, x], dim=1)
        x = self.fc(x)
        x = self.activation(x)
        x = self.dropout(x)

        # Get the logits
        return self.logits(x)


if __name__ == '__main__':
    model = OutcomePredictor(10)
    x = torch.tensor([[1, 2]], dtype=torch.long)
    out = model(x)
    # print(out.shape)
