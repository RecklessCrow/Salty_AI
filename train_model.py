import os
from datetime import datetime

import keras
import numpy as np
import tensorflow as tf
from keras.callbacks import LearningRateScheduler, ModelCheckpoint, TensorBoard
from keras.layers import Dense, BatchNormalization, Dropout, LSTM
from keras.models import Sequential
from sklearn.preprocessing import OneHotEncoder

physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

label_encoder = OneHotEncoder()


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


def data_generator(batch_size):
    while True:
        x = []
        y = []

        for i in range(batch_size):
            pass

        yield x, y


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

    # Train model
    model.fit(
        data_generator(batch_size=50),
        epochs=epochs,
        callbacks=[tensorboard_callback, checkpoint_callback, scheduler_callback],
        batch_size=10000
    )

    if save_to is None:
        keras.models.save_model(model, os.path.join('models', curr_date))
    else:
        keras.models.save_model(model, save_to)


if __name__ == '__main__':
    train()
