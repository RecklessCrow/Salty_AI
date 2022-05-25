import numpy as np
from tensorflow.keras.utils import Sequence


class DataGenerator(Sequence):
    def __init__(self, x, y, train=False, batch_size=32, shuffle=True, seed=None):
        """
        :param x:
        :param y:
        :param batch_size:
        :param shuffle:
        """

        self.x, self.y = x, y
        self.train = train
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.rng = np.random.default_rng(seed=seed)

    def __len__(self):
        return len(self.x) // self.batch_size

    def __getitem__(self, idx):
        batch_x = self.x[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.y[idx * self.batch_size:(idx + 1) * self.batch_size]

        # Randomly switch red and blue teams to correct for potential class imbalance at a per character level
        if self.rng.random() > 0.5 and self.train:
            batch_x = np.flip(batch_x, axis=1)
            batch_y = (batch_y + 1) % 2

        # Randomly mask characters out to help when unknown characters are in matches
        if self.rng.random() > 0.9 and self.train:
            self.x[:][int(np.around(self.rng.random()))] = 0

        return batch_x, batch_y

    def on_epoch_end(self):
        """
        Shuffle data
        :return:
        """
        if self.shuffle:
            idxs = np.arange(len(self.x))
            self.rng.shuffle(idxs)
            self.x = self.x[idxs]
            self.y = self.y[idxs]
