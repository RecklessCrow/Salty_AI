import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from datetime import datetime

import keras.saving.saved_model.model_serialization
from keras import Input
from keras.callbacks import EarlyStopping
from keras.layers import Dense, Embedding, Flatten, MultiHeadAttention, Dropout, LayerNormalization
from keras_tuner import HyperModel, HyperParameters, Hyperband
from tensorflow.keras.optimizers import Adam

# Training
EPOCHS = 100
STEPS = 256
LOSS = "bce"

# Early Stopping
min_delta = 0.01
patience = 3


def make_embedding_model(parameters):
    inputs = Input(shape=(2,))
    x = Embedding(input_dim=parameters["input_dim"], output_dim=parameters["embedding_out"])(inputs)
    x = Flatten()(x)

    for _ in range(parameters["ff_layers"]):
        x = Dense(
            units=parameters["ff_units"],
            activation=parameters["ff_activation"]
        )(x)
        x = Dropout(parameters["dropout"])(x)

    outputs = Dense(units=1, activation="sigmoid")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="salty_model")

    model.compile(
        optimizer=Adam(
            learning_rate=parameters["learning_rate"],
            epsilon=parameters["epsilon"]
        ),
        loss=LOSS,
        metrics=["accuracy"]
    )

    return model


def make_attention_model(parameters):
    inputs = Input(shape=(2,))
    x = Embedding(input_dim=parameters["input_dim"], output_dim=parameters["embedding_out"])(inputs)

    # Transformer
    for _ in range(parameters["num_transformers"]):
        # Attention
        sub_x = MultiHeadAttention(
            num_heads=parameters["attention_heads"],
            key_dim=parameters["attention_keys"],
            dropout=parameters["dropout"]
        )(x, x)
        x = LayerNormalization()(x + sub_x)

        # Feed Forward
        sub_x = Dense(
            units=parameters["embedding_out"],
            activation=parameters["ff_activation"]
        )(x)
        x = LayerNormalization()(x + sub_x)

        x = Dropout(parameters["dropout"])(x)

    x = Flatten()(x)

    for _ in range(parameters["ff_layers"]):
        x = Dense(
            units=parameters["ff_units"],
            activation=parameters["ff_activation"]
        )(x)
        x = Dropout(parameters["dropout"])(x)

    outputs = Dense(units=1, activation="sigmoid")(x)

    model = keras.Model(inputs=inputs, outputs=outputs, name="salty_model")

    model.compile(
        optimizer=Adam(
            learning_rate=parameters["learning_rate"],
            epsilon=parameters["epsilon"]
        ),
        loss=LOSS,
        metrics=["accuracy"]
    )

    return model


class TuningModel(HyperModel):
    def __init__(self, input_dim):
        super().__init__()
        self.input_dim = input_dim

    def build(self, hp: HyperParameters):
        hp_dropout = 0.0
        hp_output_dim = hp.Choice("Embedding Outputs", [2 ** p for p in range(2, 10)])
        hp_transformers = hp.Int("Transformers", min_value=1, max_value=5)
        hp_heads = hp.Int("Attention Heads", min_value=1, max_value=5)
        hp_key_dim = hp.Int("Key Dimention", min_value=1, max_value=5)
        hp_layers = hp.Int("Dense Layers", min_value=1, max_value=5)
        hp_units = hp.Choice("Dense Units", [2 ** p for p in range(2, 10)])
        hp_lr = hp.Float("Learning Rate", min_value=1e-10, max_value=1)
        hp_epsilon = hp.Float("Epsilon", min_value=1e-10, max_value=1)

        parameters = {
            "dropout": hp_dropout,
            "input_dim": self.input_dim,
            "embedding_out": hp_output_dim,
            "num_transformers": hp_transformers,
            "attention_heads": hp_heads,
            "attention_keys": hp_key_dim,
            "ff_layers": hp_layers,
            "ff_units": hp_units,
            "ff_activation": "gelu",
            "learning_rate": hp_lr,
            "epsilon": hp_epsilon
        }

        return make_attention_model(parameters)

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
            epochs=EPOCHS,
            steps_per_epoch=STEPS,
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

        parameters = {
            "dropout": 0.6,
            "input_dim": self.input_dim,
            "embedding_out": 32,
            "num_transformers": 6,
            "attention_heads": 12,
            "attention_keys": 12,
            "ff_layers": 2,
            "ff_units": 64,
            "ff_activation": "gelu",
            "learning_rate": 1e-5,
            "epsilon": 1e-7
        }

        model = make_attention_model(parameters)

        model.summary()

        return model

    def train(self, x, y, val=None):

        history = self.model.fit(
            x, y,
            validation_data=val,
            epochs=EPOCHS,
            steps_per_epoch=STEPS,
        )

        return history

    def predict(self, x):
        return self.model.predict(x)

    def save(self):
        self.model.save(os.path.join("SavedModels", f"model_{datetime.now().strftime('%H.%M.%S')}"))

    def load(self, filepath):
        self.model = keras.models.load_model(filepath)
