import os
from datetime import datetime

from keras_tuner import HyperModel, HyperParameters, Hyperband
from tensorflow.keras import Model as TF_Model
from tensorflow.keras.activations import sigmoid
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Input, Dense, Embedding, Flatten, MultiHeadAttention, Dropout, LayerNormalization
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.models import load_model
from tensorflow.keras.optimizers import Adam

from .data_generator import DataGenerator

# Training
EPOCHS = 100
BATCH_SIZE = 2 ** 13

# Early Stopping
MIN_DELTA = 0.001
PATIENCE = 3
MONITOR = "val_accuracy"


def make_embedding_model(parameters):
    """
    Model with an embedding layer and a feed forward neural network
    :param parameters:
    :return:
    """

    inputs = Input(shape=(2,))
    x = Embedding(input_dim=parameters["input_dim"], output_dim=parameters["embedding_out"])(inputs)
    x = Flatten()(x)

    for _ in range(parameters["ff_layers"]):
        x = Dense(
            units=parameters["ff_units"],
            activation=parameters["ff_activation"]
        )(x)
        x = Dropout(parameters["dropout"])(x)

    outputs = Dense(units=1)(x)

    model = TF_Model(inputs=inputs, outputs=outputs, name="salty_model")

    model.compile(
        optimizer=Adam(
            learning_rate=parameters["learning_rate"],
            epsilon=parameters["epsilon"]
        ),
        loss=BinaryCrossentropy(
            from_logits=True,
            label_smoothing=0.5
        ),
        metrics=["accuracy"]
    )

    return model


def make_attention_model(parameters):
    """
    Model with the transformer architecture
    :param parameters:
    :return:
    """

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

    # Feed forward neural network
    for _ in range(parameters["ff_layers"]):
        x = Dense(
            units=parameters["ff_units"],
            activation=parameters["ff_activation"]
        )(x)
        x = Dropout(parameters["dropout"])(x)

    outputs = Dense(units=1)(x)

    model = TF_Model(inputs=inputs, outputs=outputs, name="salty_model")

    model.compile(
        optimizer=Adam(
            learning_rate=parameters["learning_rate"],
            epsilon=parameters["epsilon"]
        ),
        loss=BinaryCrossentropy(
            from_logits=True,
            label_smoothing=0.5
        ),
        metrics=["accuracy"]
    )

    return model


class TuningModel(HyperModel):
    def __init__(self, input_dim):
        super().__init__()
        self.input_dim = input_dim

    def build(self, hp: HyperParameters):
        hp_dropout = 0.0
        hp_output_dim = hp.Choice("Embedding Outputs", [2 ** p for p in range(2, 5)])
        hp_transformers = hp.Int("Transformers", min_value=4, max_value=16)
        hp_heads = hp.Int("Attention Heads", min_value=4, max_value=12)
        hp_key_dim = hp.Int("Key Dimention", min_value=4, max_value=12)
        hp_layers = hp.Int("Dense Layers", min_value=1, max_value=8)
        hp_units = hp.Choice("Dense Units", [2 ** p for p in range(4, 11)])
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

    def search(self, x, y, val=None, epochs=EPOCHS):
        train = DataGenerator(x, y, BATCH_SIZE)

        tuner = Hyperband(
            self,
            objective="val_accuracy",
            directory=os.path.join("src", "Model"),
            project_name="parameters"
        )

        early_stopping = EarlyStopping(
            min_delta=MIN_DELTA,
            patience=PATIENCE,
            monitor=MONITOR,
            restore_best_weights=True
        )

        if val is not None:
            val = DataGenerator(val[0], val[1], batch_size=BATCH_SIZE // 8)

        tuner.search(
            train,
            validation_data=val,
            epochs=epochs,
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
            "dropout": 0.0,
            "input_dim": self.input_dim,
            "embedding_out": 32,
            "num_transformers": 8,
            "attention_heads": 8,
            "attention_keys": 8,
            "ff_layers": 4,
            "ff_units": 64,
            "ff_activation": "gelu",
            "learning_rate": 0.01,
            "epsilon": 0.001
        }

        model = make_attention_model(parameters)

        model.summary()

        return model

    def train(self, x, y, val=None, epochs=EPOCHS):
        train = DataGenerator(x, y, BATCH_SIZE)

        callbacks = []

        if val is not None:
            early_stopping = EarlyStopping(
                min_delta=MIN_DELTA,
                patience=PATIENCE,
                monitor=MONITOR,
                restore_best_weights=True
            )
            callbacks.append(early_stopping)

        if val is not None:
            val = DataGenerator(val[0], val[1], batch_size=BATCH_SIZE // 8)

        history = self.model.fit(
            train,
            validation_data=val,
            epochs=epochs,
            callbacks=callbacks
        )

        return history

    def predict(self, x, **kwargs):
        predictions = self.model.predict(x, **kwargs)
        return sigmoid(predictions).numpy()

    def save(self):
        if not os.path.isdir("saved_models"):
            os.mkdir("saved_models")
        self.model.save(os.path.join("saved_models", f"model_{datetime.now().strftime('%H.%M.%S')}"))

    def load(self, filepath):
        self.model = load_model(filepath)
