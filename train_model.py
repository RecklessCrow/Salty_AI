import os
from datetime import datetime

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import keras
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import LearningRateScheduler, ModelCheckpoint, TensorBoard
from tensorflow.keras.layers import Dense, LSTM, Dropout, BatchNormalization
from tensorflow.keras.models import Sequential
from sklearn.model_selection import train_test_split

import database_handler

physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

np.set_printoptions(precision=2, suppress=True)

# input format [win_rate, num_matches, life, meter, is.TierX, is.TierS, is.TierA, is.TierB, is.TierP]

x, y = database_handler.select_all_matches()

print(x.shape)
# x = np.dstack((x, np.zeros((len(x), 2, 5))))
# print(x[0])

x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2, random_state=66)

print(x_train.shape)

del x, y


def make_model():
    model = Sequential()

    model.add(LSTM(
        units=32,
        activation='relu',
        return_sequences=True,
    ))

    model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(LSTM(
        units=32,
        activation='relu',
        return_sequences=True,
    ))

    model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(LSTM(
        units=64,
        activation='relu',
        return_sequences=True,
    ))

    model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(LSTM(
        units=64,
        activation='relu',
        return_sequences=False,
    ))

    model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(Dense(
        units=8,
        activation='relu',
    ))

    model.add(BatchNormalization())
    model.add(Dropout(0.4))

    model.add(Dense(
        units=8,
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


def train(load_file=None, save_to=None):
    # Create callbacks
    curr_date = datetime.now().strftime("%Y-%m-%d_%H-%M") + '.h5'
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
        model = tf.keras.models.load_model(load_file)

    epochs = 15
    batch_size = 1000

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
        tf.keras.models.save_model(model, os.path.join('models', curr_date))
    else:
        tf.keras.models.save_model(model, save_to)

    test_model(os.path.join('models', curr_date))


def test_model(model_file):

    model = tf.keras.models.load_model(model_file)
    brackets = np.linspace(.5, 1, 10)
    results = []

    for bracket in brackets:
        bets = 0
        correct = 0
        wrong = 0
        for idx, pred in enumerate(model.predict(x_val)):

            if np.max(pred) < bracket:
                continue

            bets += 1

            if np.argmax(pred) == np.argmax(y_val[idx]):
                correct += 1
            else:
                wrong += 1

        results.append([bets, correct, wrong])

    for bracket, (bets, correct, wrong) in zip(brackets, results):
        print(
            f'Number bets > {bracket:.2%} certainty:                  {bets}\n'
            f'Percent matches > {bracket:.2%} certainty:              {bets / len(x_val):.2%}\n'
            f'Number correct matches > {bracket:.2%} certainty:       {correct}\n'
            f'Percent correct matches > {bracket:.2%} certainty:      {correct / bets:.2%}\n'
            f'Number wrong bets > {bracket:.2%} certainty:            {wrong}\n'
            f'Percent wrong > {bracket:.2%} certainty:                {wrong / bets:.2%}\n'
            )


if __name__ == '__main__':
    train()
