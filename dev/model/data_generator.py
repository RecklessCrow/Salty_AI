import numpy as np
from tensorflow.keras.utils import Sequence

from dev.model.utils import ModelConstants


class DataGenerator(Sequence):
    def __init__(self, x, y, train=False, batch_size=32, shuffle=True, seed=None):
        """
        :param x: List of input data
        :param y: List of output data
        :param batch_size: Batch size
        :param shuffle: Shuffle data
        :param seed: Random seed
        """

        self.x, self.y = x, y
        self.batch_size = batch_size
        self.train = train
        self.shuffle = shuffle
        self.rng = np.random.default_rng(seed=seed)
        self.on_epoch_end()

    def __len__(self):
        return np.ceil(len(self.x) / self.batch_size).astype(int)

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        # Randomly switch red and blue teams to correct for potential class imbalance at a per character level
        if self.rng.random() > 0.5 and self.train:
            batch_x = np.flip(batch_x, axis=1)
            batch_y = (batch_y + 1) % 2

        # Randomly mask characters out to help when unknown characters are in matches
        if self.train:
            idxs = self.rng.integers(2, size=(len(batch_x)))
            batch_x[idxs, self.rng.choice([0, 1])] = ModelConstants.UNKNOWN_FIGHTER

        return batch_x, batch_y

    def on_epoch_end(self):
        """
        Shuffle database on epoch end
        """
        if self.shuffle:
            idxs = np.arange(len(self.x))
            self.rng.shuffle(idxs)
            self.x = self.x[idxs]
            self.y = self.y[idxs]

    def __bool__(self):
        return True
