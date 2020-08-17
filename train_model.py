import os
from datetime import datetime

import keras
import numpy as np
import tensorflow as tf
from keras.callbacks import LearningRateScheduler, ModelCheckpoint, TensorBoard
from keras.layers import Dense, BatchNormalization, Dropout, LSTM
from keras.models import Sequential
from sklearn.preprocessing import OneHotEncoder, Normalizer
from sklearn.model_selection import train_test_split
from tqdm import tqdm

import database_handler

physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

normalizer = Normalizer()
label_encoder = OneHotEncoder()
label_encoder.fit([[0], [1]])

x = []
y = []
matches = database_handler.select_all_matches()
for output in tqdm(matches, total=len(matches)):
    matchup = output[:16]
    winner = output[16]
    matchup = [0 if element is None else element for element in matchup]
    x.append(matchup)
    y.append([winner])

# x = normalizer.transform(x)
x = np.array(x).astype('float64').reshape((-1, 2, 8))
y = label_encoder.transform(y).toarray()

x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2)

del x, y


def make_model():
    model = Sequential()

    model.add(LSTM(
        units=256,
        activation='relu',
        return_sequences=True,
    ))

    model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(LSTM(
        units=256,
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
        loss='mae',
        metrics=['categorical_accuracy']
    )

    return model


def scheduler(epoch):
    if epoch < 3:
        return 0.001
    return 0.001 * np.exp(0.1 * (3 - epoch))


def data_generator(batch_size=50):
    while True:
        x = []
        y = []

        for matchup in database_handler.select_rand_match(batch_size):
            char_info = matchup[:16]
            label = matchup[16]
            char_info = [0 if element is None else element for element in char_info]
            x.append(char_info)
            y.append([label])

        # x = normalizer.transform(x)
        x = np.array(x).astype('float64').reshape((-1, 2, 8))
        y = label_encoder.transform(y).toarray()

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

    epochs = 100
    steps_per_epoch = 1000
    batch_size = 5000

    # Train model

    model.fit(
        x=x_train,
        y=y_train,
        epochs=epochs,
        validation_data=(x_val, y_val),
        callbacks=[tensorboard_callback, checkpoint_callback, scheduler_callback],
    )

    # model.fit(
    #     data_generator(batch_size=batch_size),
    #     epochs=epochs,
    #     steps_per_epoch=steps_per_epoch,
    #     validation_data=(x_val, y_val),
    #     callbacks=[tensorboard_callback, checkpoint_callback, scheduler_callback],
    # )

    if save_to is None:
        keras.models.save_model(model, os.path.join('models', curr_date))
    else:
        keras.models.save_model(model, save_to)


if __name__ == '__main__':
    train()
