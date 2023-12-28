import torch
from torch import nn


class ComplexCardioid(nn.Module):
    def __init__(self):
        super(ComplexCardioid, self).__init__()

    def forward(self, z):
        angle = torch.angle(z)
        magnitude = 1 + torch.cos(angle)
        return magnitude * z / 2.0


class ComplexModel(nn.Module):
    def __init__(self, num_tokens, num_classes, e_dim=512, dropout=0.5):
        super(ComplexModel, self).__init__()

        self.embedding = nn.Embedding(num_tokens, e_dim)
        self.fc = nn.Linear(e_dim, e_dim // 2, dtype=torch.cfloat)
        self.logits = nn.Linear(e_dim // 2, num_classes)
        self.complex_activation = ComplexCardioid()
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        r, b = x[:, 0], x[:, 1]

        # Get embeddings for each fighter
        r = self.embedding(r)
        b = self.embedding(b)

        # Combine embeddings as complex numbers
        z = r + (b * 1j)
        z = self.fc(z)
        z = self.complex_activation(z)

        # Transform back to real numbers by
        # taking the softmax of the magnitude and the softmax of the angle
        # and averaging the two
        x = self.softmax(torch.abs(z)) + self.softmax(torch.angle(z))
        x /= 2.0

        return self.logits(x)
