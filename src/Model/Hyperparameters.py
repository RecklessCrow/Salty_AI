"""
Hyperparameters for the neural network
"""

embedding_output = 4

dense_layers = 2
dense_units = 128
dense_activation = "gelu"

dropout = 0.6

optimizer = "adam"
loss = "bce"

epochs = int(1e6)
validation_split = 0.1
