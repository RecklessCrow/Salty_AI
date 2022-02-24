import os
from datetime import datetime

import keras.saving.saved_model.model_serialization
from keras.callbacks import EarlyStopping
from keras.layers import Dense, Embedding, Flatten
from keras_tuner import HyperModel, HyperParameters, Hyperband
from tensorflow.keras import Sequential
from tensorflow.keras.optimizers import Adam, Nadam, Adamax, Adagrad, Adadelta, RMSprop

from src.Model.Hyperparameters import *


class TuningModel(HyperModel):
    def __init__(self, input_dim):
        super().__init__()
        self.input_dim = input_dim

    def build(self, hp: HyperParameters):
        model = Sequential()

        hp_output_dim = hp.Int("embedding_outputs", min_value=1, max_value=5)
        model.add(Embedding(
            input_dim=self.input_dim,
            output_dim=hp_output_dim,
            input_length=2
        ))

        model.add(Flatten())

        hp_layers = hp.Int("num_dense", min_value=1, max_value=5)
        hp_units = hp.Choice(f"dense_units", [2 ** p for p in range(4, 10)])
        for num_dense in range(hp_layers):
            model.add(Dense(
                units=hp_units,
                activation=dense_activation
            ))

        model.add(Dense(
            units=1,
            activation="sigmoid"
        ))

        optimizers = [Adam, Nadam, Adamax, Adagrad, Adadelta, RMSprop]
        hp_optimizer_idx = hp.Int("optimizer_idx", min_value=0, max_value=len(optimizers) - 1)
        hp_lr = hp.Float("LR", min_value=1e-6, max_value=0.1)

        model.compile(
            optimizer=optimizers[hp_optimizer_idx](learning_rate=hp_lr),
            loss=loss,
            metrics=["accuracy"]
        )

        return model

    def search(self, x, y):
        tuner = Hyperband(
            self,
            objective="val_accuracy",
            directory=os.path.join("src", "Model"),
            project_name="parameters"
        )

        early_stopping = EarlyStopping(
            min_delta=min_delta,
            patience=patience,
            restore_best_weights=True
        )

        tuner.search(
            x, y,
            epochs=epochs,
            validation_split=validation_split,
            steps_per_epoch=32,
            callbacks=[early_stopping]
        )

        return tuner.get_best_hyperparameters()


class Model:
    def __init__(self, input_dim, filepath=None):
        self.input_dim = input_dim
        self.model = None

        if filepath is None:
            self.model = self.build()
        else:
            self.load(filepath)

    def build(self):
        model = Sequential()

        model.add(Embedding(
            input_dim=self.input_dim,
            output_dim=embedding_output,
            input_length=2
        ))

        model.add(Flatten())

        for _ in range(dense_layers):
            model.add(Dense(
                units=dense_units,
                activation=dense_activation
            ))

        # output layer
        model.add(Dense(
            units=1,
            activation="sigmoid"
        ))

        model.compile(
            optimizer=Adam(learning_rate=learning_rate),
            loss=loss,
            metrics=["accuracy"]
        )

        return model

    def train(self, x, y):

        history = self.model.fit(
            x, y,
            epochs=epochs,
            steps_per_epoch=32,
        )

        self.save()

        return history

    def predict(self, x):
        return self.model.predict(x)

    def save(self):
        self.model.save(os.path.join("SavedModels", f"model_{datetime.now().strftime('%H.%M.%S')}"))

    def load(self, filepath):
        self.model = keras.models.load_model(filepath)
