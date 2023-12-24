import torch
import torch.nn as nn
from torch_geometric.nn import GraphConv


class CharacterGNN(nn.Module):
    def __init__(self, num_nodes, embedding_dim, hidden_dim, num_classes):
        super(CharacterGNN, self).__init__()
        self.embedding = nn.Embedding(num_nodes, embedding_dim)
        self.conv1 = GraphConv(in_channels=embedding_dim, out_channels=hidden_dim)
        self.conv2 = GraphConv(in_channels=hidden_dim, out_channels=num_classes)
        self.fc = nn.Linear(num_classes, 2)

        # Hardcoded edge index for two nodes in each graph
        self.edge_index = torch.tensor([[0, 1], [1, 0]], dtype=torch.long).t().contiguous()

    def forward(self, x):
        x = self.embedding(x)
        x = self.conv1(x, self.edge_index)
        x = self.conv2(x, self.edge_index)
        x = x.mean(dim=1)  # Global pooling
        x = self.fc(x)
        return x


if __name__ == '__main__':
    model = CharacterGNN(10, 32, 64, 2)
    x = torch.tensor([[1, 2], [2, 9], [2, 9], [2, 9], [2, 9], [2, 9]], dtype=torch.long)
