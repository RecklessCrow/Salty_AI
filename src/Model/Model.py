import os
from datetime import datetime

import keras.saving.saved_model.model_serialization
from keras.callbacks import EarlyStopping
from keras.layers import Dense, Embedding, Flatten
from keras_tuner import HyperModel, HyperParameters, Hyperband
from tensorflow.keras import Sequential
from tensorflow.keras.optimizers import Adam

from src.Model.Hyperparameters import *


class TuningModel(HyperModel):
    def __init__(self, input_dim):
        super().__init__()
        self.input_dim = input_dim

    def build(self, hp: HyperParameters):
        model = Sequential()

        hp_output_dim = hp.Int("Embedding Outputs", min_value=1, max_value=10)
        model.add(Embedding(
            input_dim=self.input_dim,
            output_dim=hp_output_dim,
            input_length=2
        ))

        model.add(Flatten())

        hp_layers = hp.Int("Dense Layers", min_value=1, max_value=5)
        hp_units = hp.Choice(f"Dense Units", [2 ** p for p in range(4, 10)])
        for num_dense in range(hp_layers):
            model.add(Dense(
                units=hp_units,
                activation=dense_activation
            ))

        model.add(Dense(
            units=1,
            activation="sigmoid"
        ))

        hp_lr = hp.Float("Learning Rate", min_value=1e-10, max_value=1)
        hp_epsilon = hp.Float("Epsilon", min_value=1e-10, max_value=1)

        model.compile(
            optimizer=Adam(learning_rate=hp_lr, epsilon=hp_epsilon),
            loss=loss,
            metrics=["accuracy"]
        )

        return model

    def search(self, x, y, validation_data=None):
        validation_split = 0

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

        if validation_data is not None:
            validation_split = 0.125

        tuner.search(
            x, y,
            validation_data=validation_data,
            validation_split=validation_split,
            epochs=epochs,
            steps_per_epoch=steps,
            callbacks=[early_stopping]
        )

        return tuner.get_best_hyperparameters()


class Model:
    def __init__(self, input_dim=None, filepath=None):
        if input_dim is not None:
            self.input_dim = input_dim
            self.model = self.build()

        else:
            assert filepath is not None, "Must have one of input_dim or filepath not None"
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
            optimizer=Adam(
                learning_rate=learning_rate,
                epsilon=epsilon
            ),
            loss=loss,
            metrics=["accuracy"]
        )

        return model

    def train(self, x, y, val=None):

        history = self.model.fit(
            x, y,
            validation_data=val,
            epochs=epochs,
            steps_per_epoch=steps,
        )

        return history

    def predict(self, x):
        return self.model.predict(x)

    def save(self):
        self.model.save(os.path.join("SavedModels", f"model_{datetime.now().strftime('%H.%M.%S')}"))

    def load(self, filepath):
        self.model = keras.models.load_model(filepath)
