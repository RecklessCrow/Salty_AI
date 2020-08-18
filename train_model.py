import os
from datetime import datetime
from random import randrange

import keras
import numpy as np
import tensorflow as tf
from keras.callbacks import LearningRateScheduler, ModelCheckpoint, TensorBoard
from keras.layers import Dense, BatchNormalization, Dropout, LSTM
from keras.models import Sequential
from sklearn.model_selection import train_test_split

import database_handler

physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

np.set_printoptions(precision=2, suppress=True)


x, y = database_handler.select_all_matches()

x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2)

print(x_train.shape)

del x, y


def make_model():
    model = Sequential()

    # model.add(Input((2, 5)))

    model.add(BatchNormalization())

    model.add(LSTM(
        units=128,
        activation='relu',
        return_sequences=True,
    ))

    model.add(BatchNormalization())

    model.add(LSTM(
        units=128,
        activation='relu',
        return_sequences=False,
    ))

    model.add(BatchNormalization())

    model.add(Dense(
        units=256,
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
        loss='categorical_crossentropy',
        metrics=['categorical_accuracy']
    )

    return model


def scheduler(epoch):
    if epoch < 3:
        return 0.001
    return 0.001 * np.exp(0.1 * (3 - epoch))


def data_generator_db(batch_size=50):
    while True:
        x = []
        y = []
        for matchup in database_handler.select_rand_match(batch_size):
            char_info = matchup[:len(matchup) - 1]
            label = matchup[len(matchup) - 1]
            char_info = [0 if element is None else element for element in char_info]
            x.append(char_info)
            y.append([label])

        x = np.array(x).astype('float64').reshape((-1, 2, len(x[0]) // 2))
        y = label_encoder.transform(y).toarray()

        yield x, y


def data_generator(train=True, batch_size=50):
    while True:

        x = []
        y = []

        for i in range(batch_size):

            if train:
                idx = randrange(0, len(x_train))
                x.append(x_train[idx])
                y.append(y_train[idx])
                continue

            idx = randrange(0, len(x_val))
            x.append(x_val[idx])
            y.append(y_val[idx])

        x = np.array(x)
        y = np.array(y)

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

    epochs = 25
    steps_per_epoch = 50
    batch_size = 5000

    # Train model

    model.fit(
        x=x_train,
        y=y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(x_val, y_val),
        callbacks=[tensorboard_callback, checkpoint_callback, scheduler_callback],
    )

    # model.fit(
    #     data_generator_db(batch_size=batch_size),
    #     epochs=epochs,
    #     steps_per_epoch=steps_per_epoch,
    #     callbacks=[tensorboard_callback, checkpoint_callback, scheduler_callback],
    # )

    # model.fit(
    #     data_generator(batch_size=batch_size),
    #     epochs=epochs,
    #     steps_per_epoch=steps_per_epoch,
    #     validation_data=data_generator(train=False, batch_size=batch_size // 4),
    #     validation_steps=steps_per_epoch // 4,
    #     callbacks=[tensorboard_callback, checkpoint_callback, scheduler_callback],
    # )

    for idx, pred in enumerate(model.predict(x_val)):
        print(x_val[idx])
        print(pred, y_val[idx], '\n')

    if save_to is None:
        keras.models.save_model(model, os.path.join('models', curr_date))
    else:
        keras.models.save_model(model, save_to)


if __name__ == '__main__':
    train()
