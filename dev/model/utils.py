import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split

from src.base.base_database_handler import DATABASE

SEED = 4


def set_random_state():
    """
    set random state for consistent weight initialization
    :return:
    """
    np.random.seed(SEED)
    tf.random.set_seed(SEED)


# Data
DB = DATABASE
UNKNOWN_FIGHTER = '<unknown>'
VOCAB = np.array(DB.get_all_characters()).flatten()
dataset = np.array(DB.get_all_matches())
x, y = dataset[:, :-1], dataset[:, -1]
y = np.array([[i == "red", i == "blue"] for i in y]).astype(np.float32)
# y = (y == "red").astype(np.float32).reshape(-1, 1)  # Convert to binary
del dataset
BUCKETS = 5

# split data 70/20/10
test_size = 0.2
val_size = 0.1 / (1 - test_size)
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=SEED)
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, test_size=val_size, random_state=SEED)

# Training
BATCH_SIZE = 2 ** 12
EPOCHS = 30
MAX_TRAINING_STEPS = int(np.ceil((len(x) / BATCH_SIZE) * EPOCHS))

# Tuning
TUNER_OBJECTIVE = 'val_accuracy'
ITERATIONS = 16
FACTOR = 2

# Early Stopping
ENABLE_ES = False
ES_MIN_DELTA = 0.0001
ES_PATIENCE = 10
ES_MONITOR = "val_accuracy"
