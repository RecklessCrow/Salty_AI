"""
Hyperparameters for the neural network
"""

embedding_output = 3
dense_layers = 4
dense_units = 32
dense_activation = "gelu"

optimizer = "adam"
learning_rate = 0.03
loss = "bce"

# Training
epochs = 34
validation_split = 0.1

# Early Stopping
min_delta = 0.0001
patience = 4
