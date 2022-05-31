import os
import random

import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split

from dev.dev_database_handler import MatchDatabaseHandler

DATABASE = MatchDatabaseHandler()
SEED = 123


def set_random_state():
    """
    set random state for consistent weight initialization
    :return:
    """

    os.environ['PYTHONHASHSEED'] = str(SEED)
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)


class ModelConstants:
    """
    Constants class
    """
    # Embedding parameters
    UNKNOWN_FIGHTER = '<unknown>'
    VOCAB = np.array(DATABASE.get_all_characters()).flatten()
    EMBEDDING_INPUT_DIM = len(VOCAB) + 2  # +2 for oov and unknown tokens

    # Loss function parameters
    ALPHA = 1.0

    # Training
    BATCH_SIZE = 2 ** 12
    EPOCHS = 30
    MAX_TRAINING_STEPS = int(np.ceil((len(DATABASE.get_all_matches()) / BATCH_SIZE) * EPOCHS))

    # Tuning
    TUNER_OBJECTIVE = 'val_accuracy'
    ITERATIONS = 16
    FACTOR = 2

    # Cross validation
    CROSS_VALIDATION_FOLDS = 5

    # Early Stopping
    ENABLE_ES = False
    ES_MIN_DELTA = 0.0001
    ES_PATIENCE = 10
    ES_MONITOR = "val_accuracy"


class Dataset:
    """
    Dataset class
    """

    def __init__(self, test_size=0.2, val_size=0.0):
        """
        Initialize dataset with train and test split
        :param test_size: Percentage of the dataset to be used for testing. Default is 20%
        :param val_size: Percentage of the dataset to be used for validation. Default is 0%
        """

        dataset = np.array(DATABASE.get_all_matches())
        self.x, self.y = dataset[:, :-1], dataset[:, -1]
        self.y = np.array([[i == "red", i == "blue"] for i in self.y]).astype(np.float32)  # one hot encoding

        # Split dataset into training and test set
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(
            self.x, self.y, test_size=test_size, random_state=SEED)

        # Split training set into training and validation set if requested
        self.x_val, self.y_val = None, None
        if val_size > 0:
            self.x_train, self.x_val, self.y_train, self.y_val = train_test_split(
                self.x_train, self.y_train, test_size=val_size / (1 - test_size), random_state=SEED)

    def get_train_dataset(self):
        return self.x_train, self.y_train

    def get_test_dataset(self):
        return self.x_test, self.y_test

    def get_val_dataset(self):
        assert self.x_val is not None, "Validation set was not created"
        return self.x_val, self.y_val

    def get_whole_dataset(self):
        return self.x, self.y


if __name__ == '__main__':
    dataset = Dataset(make_val=True)
    # print(dataset.get_train_dataset())
    # print(dataset.get_test_dataset())
    print(dataset.get_val_dataset())
