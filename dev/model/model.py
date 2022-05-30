import os
from datetime import datetime

from tensorflow.keras.activations import sigmoid
from tensorflow.python.keras.callbacks import ModelCheckpoint, EarlyStopping

from dev.model.data_generator import DataGenerator
from dev.model.make_model import make_attention_model
from dev.model.utils import *


class Model:
    MODEL_DIR = "../saved_models"

    def __init__(self):
        self.model_name = f"{datetime.now().strftime('%H.%M.%S')}"
        self.model_dir = f"{self.MODEL_DIR}/{self.model_name}"
        self.model = self.__build()

    @staticmethod
    def __build():
        parameters = {
            "dropout": 0.1,
            "embedding_out": 512,
            "num_transformers": 12,
            "attention_heads": 12,
            "attention_keys": 12,
            "ff_layers": 1,
            "ff_units": 128,
            "ff_activation": "gelu",
            "epsilon": 1e-6,
            "learning_rate": 1e-4,
            "smoothing": 0.1,
        }

        model = make_attention_model(parameters)

        return model

    def train(self, x, y, val=None, epochs=EPOCHS, early_stopping=False, checkpointing=False, **kwargs):
        train = DataGenerator(x, y, train=True, batch_size=BATCH_SIZE)

        callbacks = []

        if val is not None and early_stopping:
            callbacks.append(EarlyStopping(
                monitor=ES_MONITOR,
                min_delta=ES_MIN_DELTA,
                patience=ES_PATIENCE,
                restore_best_weights=True
            ))

        if val is not None and checkpointing:
            val = DataGenerator(val[0], val[1], train=False, batch_size=BATCH_SIZE)

            callbacks.append(ModelCheckpoint(
                filepath=os.path.join(self.model_dir + "/model_checkpoint_loss"),
                monitor="val_loss",
                save_best_only=True
            ))

            callbacks.append(ModelCheckpoint(
                filepath=os.path.join(self.model_dir + "/model_checkpoint_acc"),
                monitor="val_accuracy",
                save_best_only=True
            ))

        history = self.model.fit(
            train,
            validation_data=val,
            callbacks=callbacks,
            epochs=epochs,
            **kwargs
        )

        return history

    def predict(self, x, **kwargs):
        predictions = self.model.predict(x.reshape(-1, 2), **kwargs)
        return sigmoid(predictions).numpy()

    def save(self):
        self.model.save(self.model_dir + '/model')
