import os
from datetime import datetime

from sklearn.utils.extmath import softmax
from tensorflow.python.keras.callbacks import ModelCheckpoint, EarlyStopping
from tensorflow.python.keras.models import load_model

from dev.model.data_generator import DataGenerator
from dev.model.make_model import make_attention_model
from dev.model.utils import *


class Model:
    MODEL_DIR = "../saved_models"

    def __init__(self, model_name=None):
        if model_name is not None:
            self.model_name = f"{datetime.now().strftime('%H.%M.%S')}"
            self.model_dir = f"{self.MODEL_DIR}/{self.model_name}"
            self.model = self.__build()
        else:
            self.model_name = model_name
            self.__load()

    @staticmethod
    def __build():
        parameters = {
            "dropout": 0.1,
            "embedding_out": 128,
            "num_transformers": 8,
            "attention_heads": 6,
            "attention_keys": 6,
            "ff_layers": 2,
            "ff_units": 32,
            "ff_activation": "relu",
            "epsilon": 1e-6,
            "learning_rate": 1e-3,
            "smoothing": 0.05,
        }

        model = make_attention_model(parameters)

        return model

    def __load(self):
        self.model = load_model(f"{self.MODEL_DIR}/{self.model_name}/model")

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
        predictions = self.model.predict(x, **kwargs)
        predictions = softmax(predictions)
        return predictions

    def save(self):
        self.model.save(self.model_dir + '/model')
