import os
import time
from datetime import datetime

import keras
import numpy as np
import pandas as pd
import tensorflow as tf
from keras.layers import Dense, BatchNormalization, Dropout, Conv1D
from keras.models import Sequential
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelBinarizer

from data_generator import preprocessor

physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

label_encoder = LabelBinarizer()

red_data = pd.read_csv(os.path.join('data', 'red_data.csv'))
red_data = np.array(red_data)
red_data = red_data[:, 1:]

blue_data = pd.read_csv(os.path.join('data', 'blue_data.csv'))
blue_data = np.array(blue_data)
blue_data = blue_data[:, 1:]

labels = pd.read_csv(os.path.join('data', 'labels.csv'))
labels = np.array(labels)
labels = labels[:, 1:]
label_encoder.fit_transform(labels)
labels = label_encoder.transform(labels)

data = []
for i in range(len(red_data)):
    temp = list(red_data[i])
    temp.extend(list(blue_data[i]))
    data.append(temp)

data = np.array(data)

x_train, x_val, y_train, y_val = train_test_split(data, labels, test_size=0.2, shuffle=False)

character_lookup = pd.read_csv(os.path.join('data', 'character_lookup.csv'))

del red_data
del blue_data
del data


def encode_input(red, blue):
    a = character_lookup.loc[character_lookup['character'] == red].to_numpy()
    b = character_lookup.loc[character_lookup['character'] == blue].to_numpy()

    if a.size == 0:
        return None, None
    if b.size == 0:
        return None, None

    a = np.array(a[:, 2:]).astype('float64')
    b = np.array(b[:, 2:]).astype('float64')
    a = preprocessor.transform(a)
    b = preprocessor.transform(b)

    X = list(a[0])
    X.extend(list(b[0]))

    return X


def make_model():
    model = Sequential()

    model.add(Dense(
        units=256,
        activation='relu',
    ))

    model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(Dense(
        units=512,
        activation='relu',
    ))

    model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(Dense(
        units=512,
        activation='relu',
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


def train(load_file=None, save_to=None):
    # Create callbacks
    curr_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
    log_dir = os.path.join('logs', 'scalars', curr_date)
    tensorboard_callback = keras.callbacks.TensorBoard(log_dir=log_dir)
    checkpoint_file = os.path.join('checkpoints', curr_date)
    checkpoint_callback = keras.callbacks.ModelCheckpoint(filepath=checkpoint_file, monitor='val_accuracy',
                                                          verbose=1, save_best_only=True, mode='max')

    epochs = 25

    # Create model
    # Load checkpoint if exists
    if load_file is not None:
        model = keras.models.load_model(load_file)
    else:
        model = make_model()

    # Train model
    model.fit(
        x=x_train,
        y=y_train,
        epochs=epochs,
        validation_data=(x_val, y_val),
        callbacks=[tensorboard_callback, checkpoint_callback]
    )

    if save_to is not None:
        keras.models.save_model(model, save_to)


def data_generator(batch_size):
    import web_scraper
    web_scraper.login()
    last_red = ''
    last_blue = ''
    while True:
        x = []
        y = []
        match_num = 0
        while match_num < batch_size:
            red, blue = web_scraper.get_reb_blue()

            #  todo fix busy block
            if red == last_red and blue == last_blue:
                time.sleep(5)
                continue

            last_red = red
            last_blue = blue

            #  todo increment num_matches and num_wins for character and author across dataset

            x.append(encode_input(red, blue))
            winner = ''
            while web_scraper.get_bet_status() is None:
                winner = web_scraper.get_bet_status()
            y.append(winner)
            match_num += 1

        yield x


def train_live(epochs=25, steps_per_epoch=25, batch_size=10, load_file=None, save_to=None):
    # Create callbacks
    curr_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
    log_dir = os.path.join('logs', 'scalars', curr_date)
    tensorboard_callback = keras.callbacks.TensorBoard(log_dir=log_dir)
    checkpoint_file = os.path.join('checkpoints', curr_date)
    checkpoint_callback = keras.callbacks.ModelCheckpoint(filepath=checkpoint_file, monitor='val_accuracy',
                                                          verbose=1, save_best_only=True, mode='max')

    # Create model
    # Load checkpoint if exists
    if load_file is not None:
        model = keras.models.load_model(load_file)
    else:
        model = make_model()

    # Train model
    model.fit(
        data_generator(batch_size),
        epochs=epochs,
        steps_per_epoch=steps_per_epoch,
        callbacks=[tensorboard_callback, checkpoint_callback]
    )

    if save_to is not None:
        keras.models.save_model(model, save_to)


if __name__ == '__main__':
    train_live(load_file='checkpoints/2020-08-16_00-14')
