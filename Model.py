import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from tqdm import tqdm

# Suppress TF info messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from sklearn.metrics import classification_report
from tensorflow.keras import Sequential
from tensorflow.keras.callbacks import TensorBoard, LearningRateScheduler
from tensorflow.keras.layers import Dense, Dropout, LSTM, BatchNormalization
from sklearn.model_selection import train_test_split


# Fix TF for whatever reason
physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

time_stamp = datetime.now().strftime('%H-%M-%S')

# character_dict = {}
# author_dict = {}
# df = pd.read_csv(os.path.join('data', 'character_information.csv'))
# df.fillna(-1, inplace=True)
#
# for idx, (character_id, name, author, width, height) in tqdm(df.iterrows(), total=len(df), desc='Making dictionaries'):
#     if author not in author_dict:
#         if author in ['null', 'Notfound']:
#             author_dict[author] = -1
#         else:
#             author_dict[author] = idx
#
#     # character_id, author_id, widht, height, wins, matches
#     character_dict[name] = [character_id, author_dict[author], width, height, 0, 0]
#
# df = pd.read_csv(os.path.join('data', 'match_data.csv'), index_col=0)
# match_history = []
# labels = []
# for idx, (match_id, red, blue, winner_id) in tqdm(df.iterrows(), total=len(df), desc='Making dictionaries'):
#
#     red_info = character_dict[red]
#     blue_info = character_dict[blue]
#
#     red_info[5] += 1
#     blue_info[5] += 1
#
#     if winner_id == 'red':
#         red_info[4] += 1
#     else:
#         blue_info[4] += 1
#
#     character_dict[red] = red_info
#     character_dict[blue] = blue_info
#
# for idx, (match_id, red, blue, winner_id) in tqdm(df.iterrows(), total=len(df), desc='Making dictionaries'):
#     red_info = character_dict[red]
#     red_info = red_info[0], red_info[1], red_info[2], red_info[3], (red_info[4] / red_info[5]) * 100
#     blue_info = character_dict[blue]
#     blue_info = blue_info[0], blue_info[1], blue_info[2], blue_info[3], (blue_info[4] / blue_info[5]) * 100
#     label = 0 if winner_id == 'Red' else 1
#     match_history.append([np.array(red_info, dtype=np.float32), np.array(blue_info, dtype=np.float32)])
#     labels.append([label])
#
# match_history = np.array(match_history)
# labels = np.array(labels, dtype=np.float32)
#
data_file = os.path.join('data', 'data.npy')
label_file = os.path.join('data', 'labels.npy')
#
# np.save(data_file, match_history)
# np.save(label_file, labels)
#
match_history, labels = np.load(data_file, allow_pickle=True), np.load(label_file, allow_pickle=True)
training_data, test_data, training_labels, test_labels = train_test_split(match_history, labels, test_size=0.2, random_state=66)


class Model:
    def __init__(self):
        self.model = self._make_model()

    @staticmethod
    def _make_model():
        model = Sequential()

        model.add(LSTM(
            units=32,
            return_sequences=True,
        ))

        model.add(BatchNormalization())
        model.add(Dropout(0.4))

        model.add(LSTM(
            units=32,
            return_sequences=True,
        ))

        model.add(BatchNormalization())
        model.add(Dropout(0.4))

        model.add(LSTM(
            units=64,
            return_sequences=False,
        ))

        model.add(BatchNormalization())
        model.add(Dropout(0.4))

        model.add(Dense(
            units=256,
            activation='gelu'
        ))

        model.add(BatchNormalization())
        model.add(Dropout(0.4))

        model.add(Dense(
            units=1,
            activation='sigmoid'
        ))

        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        return model

    def train(self):
        self.model.fit(
            x=training_data,
            y=training_labels,
            steps_per_epoch=10,
            epochs=10_000,
            validation_split=0.2,
            validation_steps=1,
            callbacks=[
                TensorBoard(f"logs/{time_stamp}"),
                LearningRateScheduler(lambda e: max(0.002 * np.exp(0.05 * -e), .00001))
            ],
            use_multiprocessing=True,
            workers=8
        )

        self.save()

    def test(self):
        y_true = test_labels
        y_pred = np.around(self.model.predict(test_data))

        print(classification_report(y_true, y_pred, zero_division=True))

    def load(self, filename):
        self.model = tf.keras.models.load_model(filename)

    def save(self):
        self.model.save(os.path.join('models', 'trained', time_stamp))


if __name__ == '__main__':
    a = Model()
    a.train()
    # a.load('models/trained/00-16-08')
    a.test()
