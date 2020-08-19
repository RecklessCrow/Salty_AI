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

x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2, random_state=66)

print(x_train.shape)

del x, y


def make_model():
    model = Sequential()

    # model.add(Input((2, 5)))

    model.add(LSTM(
        units=16,
        activation='relu',
        return_sequences=True,
    ))

    # model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(LSTM(
        units=32,
        activation='relu',
        return_sequences=False,
    ))

    # model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(Dense(
        units=64,
        activation='relu',
    ))

    # model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(Dense(
        units=2,
        activation='softmax'
    ))

    model.compile(
        optimizer='adam',
        loss='msle',
        metrics=['categorical_accuracy']
    )

    return model


def scheduler(epoch):
    if epoch < 3:
        return 0.001
    return 0.001 * np.exp(0.1 * (3 - epoch))


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

    if save_to is None:
        keras.models.save_model(model, os.path.join('models', curr_date))
    else:
        keras.models.save_model(model, save_to)

    test_model(os.path.join('models', curr_date))


def test_model(model_file):

    model = keras.models.load_model(model_file)

    wrong = 0
    upset = 0
    bets = 0
    big_loss = 0

    for idx, pred in enumerate(model.predict(x_val)):

        if np.max(pred) < 0.55:
            continue

        bets += 1

        if np.argmax(pred) == np.argmax(y_val[idx]):
            continue

        wrong += 1

        if np.max(pred) < 0.60:
            continue

        upset += 1

        if np.max(pred) < 0.75:
            continue

        big_loss += 1

    print(
        f'Number of matches:                        {len(x_val)}\n\n'          
        f'Number bets > 55% certainty:              {bets}\n'
        f'Percent bets:                             {bets / len(x_val):.2%}\n\n'
        f'Number wrong bets:                        {wrong}\n'
        f'Percent wrong to bets                     {wrong / bets:.2%}\n\n'
        f'Number of wrong upset > 60% certainty:    {upset}\n'
        f'Percent upset to bets:                    {upset / bets:.2%}\n'
        f'Percent upset:                            {upset / len(x_val):.2%}\n\n'
        f'Number of BIG Losses > 75% certainty:     {big_loss}\n'
        f'Percent BIG Losses to bets:               {big_loss / bets:.2%}\n'
        f'Percent BIG Losses:                       {big_loss / len(x_val):.2%}\n\n'
        f'\n'
        )


if __name__ == '__main__':
    # train()
    test_model('models/2020-08-18_19-40')
