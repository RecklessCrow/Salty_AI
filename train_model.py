import os
import random
from datetime import datetime

import keras
import numpy as np
import tensorflow as tf
from keras.callbacks import LearningRateScheduler, ModelCheckpoint, TensorBoard
from keras.layers import Dense, BatchNormalization, Dropout, LSTM
from keras.models import Sequential
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, Normalizer
from tqdm import tqdm

import database_handler
import web_scraper

physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

normalizer = Normalizer()
label_encoder = OneHotEncoder()
label_encoder.fit([[0], [1]])


def make_model():
    model = Sequential()

    model.add(LSTM(
        units=128,
        activation='relu',
        return_sequences=True
    ))

    model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(LSTM(
        units=128,
        activation='relu',
        return_sequences=False
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
        units=512,
        activation='relu',
    ))

    model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(Dense(
        units=2,
        activation='softmax'
    ))

    model.compile(
        optimizer='adam',
        loss='mse',
        metrics=['categorical_accuracy']
    )

    return model


def scheduler(epoch):
    if epoch < 3:
        return 0.001
    return 0.001 * np.exp(0.1 * (3 - epoch))


def encode_input(red, blue):
    red = list(database_handler.select_character(red))
    blue = list(database_handler.select_character(blue))
    red.extend(blue)
    X = [0 if element is None else element for element in red]
    return np.array(X)


def data_generator_live(batch_size):
    """
    train off of live salty bet matches
    :param batch_size:
    :return:
    """

    while True:
        x = []
        y = []

        for i in range(batch_size):
            red, blue, winner = web_scraper.data_collector()
            x.append(encode_input(red, blue))

            y.append([winner])

        x = normalizer.transform(x)
        x = x.reshape((-1, 2, 8))
        y = label_encoder.transform(y).toarray()

        yield x, y


def data_generator_db(batch_size):
    """
    train directly off the data base, really slow
    :param batch_size:
    :return:
    """
    while True:
        x = []
        y = []

        for red, blue, winner in database_handler.select_rand_match(batch_size):
            x.append(encode_input(red, blue))

            y.append([winner])

        x = normalizer.transform(x)
        x = x.reshape((-1, 2, 8))
        y = label_encoder.transform(y).toarray()

        yield x, y


inputs = []
labels = []
matches = np.array(database_handler.select_all_matches())
for r, b, winner in tqdm(matches, total=len(matches)):
    inputs.append(encode_input(r, b))
    labels.append(np.array([winner]).astype('float64'))
inputs = np.array(inputs).astype('float64')
inputs = inputs.reshape((-1, 2, 8))
labels = label_encoder.transform(labels).toarray()

x_train, x_val, y_train, y_val = train_test_split(inputs, labels, test_size=0.2)


def data_generator(batch_size, train=True):
    """
    train off memory
    :param batch_size:
    :param train:
    :return:
    """
    while True:
        x = []
        y = []

        for i in range(batch_size):
            if train:
                idx = random.randrange(0, len(x_train))
                x.append(x_train[idx])
                y.append(y_train[idx])
                continue

            idx = random.randrange(0, len(x_val))
            x.append(x_val[idx])
            y.append(y_val[idx])

        yield np.array(x), np.array(y)


def train(load_file=None, save_to=None):
    # Create callbacks
    curr_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
    log_dir = os.path.join('logs', 'scalars', curr_date)
    tensorboard_callback = TensorBoard(log_dir=log_dir)
    checkpoint_file = os.path.join('checkpoints', curr_date)
    checkpoint_callback = ModelCheckpoint(filepath=checkpoint_file, monitor='val_categorical_accuracy',
                                          verbose=0, save_best_only=True, mode='max')
    scheduler_callback = LearningRateScheduler(scheduler, verbose=0)

    # Create model
    # Load checkpoint if exists
    if load_file is None:
        model = make_model()
    else:
        model = keras.models.load_model(load_file)

    epochs = 50
    steps_per_epoch = 1000
    batch_size = 5000

    # Train model

    model.fit(
        data_generator(batch_size=batch_size),
        epochs=epochs,
        steps_per_epoch=steps_per_epoch,
        validation_data=data_generator(batch_size=batch_size // 10, train=False),
        validation_steps=steps_per_epoch // 10,
        callbacks=[tensorboard_callback, checkpoint_callback, scheduler_callback],
    )

    if save_to is None:
        keras.models.save_model(model, os.path.join('models', curr_date))
    else:
        keras.models.save_model(model, save_to)


if __name__ == '__main__':
    train()
