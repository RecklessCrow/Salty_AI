import os
from datetime import datetime

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import keras.saving.saved_model.model_serialization
from keras.callbacks import EarlyStopping
from keras.layers import Dense, Embedding, Dropout, Flatten
from tensorflow.keras import Sequential

from Hyperparameters import *


class Model:
    def __init__(self, input_dim):
        self.model = self.__make_model(input_dim)

    @staticmethod
    def __make_model(input_dim):
        model = Sequential()

        model.add(Embedding(
            input_dim=input_dim,
            output_dim=embedding_output,
            input_length=2
        ))

        model.add(Flatten())

        for _ in range(dense_layers):
            model.add(Dense(
                units=dense_units,
                activation=dense_activation)
            )
            model.add(Dropout(dropout))

        # output layer
        model.add(Dense(
            units=1,
            activation="sigmoid"
        ))

        model.compile(
            optimizer=optimizer,
            loss=loss,
            metrics=["accuracy"]
        )

        print(model.summary())

        return model

    def train(self, x, y):
        self.model.fit(
            x, y,
            epochs=epochs,
            validation_split=validation_split,
            steps_per_epoch=1,
            callbacks=[
                EarlyStopping(
                    # monitor="",
                    min_delta=0.0001,
                    patience=5,
                    restore_best_weights=True
                )
            ]
        )

    def predict(self, x):
        return self.model.predict(x)

    def save(self):
        self.model.save(os.path.join("SavedModels", f"model_{datetime.now().strftime('%H.%M.%S')}"))

    def load(self, filepath):
        self.model = keras.models.load_model(filepath)
