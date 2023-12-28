import torch
import torch.nn.functional as F
from torch import nn


class BayesianLinearLayer(nn.Module):
    def __init__(self, in_features, out_features, prior_mu=0, prior_sigma=1e-6):
        super(BayesianLinearLayer, self).__init__()

        # Parameters for weight distribution
        self.prior_mu = prior_mu
        self.prior_sigma = prior_sigma

        # Learnable parameters
        self.weight_mu = nn.Parameter(torch.Tensor(out_features, in_features))
        self.weight_rho = nn.Parameter(torch.Tensor(out_features, in_features))

        # Initialize weights
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.normal_(self.weight_mu, mean=self.prior_mu, std=self.prior_sigma)
        nn.init.normal_(self.weight_rho, mean=self.prior_mu, std=self.prior_sigma)

    def forward(self, x):
        # Reparameterization trick for sampling from the weight distribution
        epsilon = torch.randn_like(self.weight_rho)
        weight = self.weight_mu + torch.log1p(torch.exp(self.weight_rho)) * epsilon

        # Compute the output
        return F.linear(x, weight)
