import os
from datetime import datetime

from sklearn.utils.extmath import softmax
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from tensorflow.keras.models import load_model
from tensorflow_addons.optimizers import RectifiedAdam

from dev.model.data_generator import DataGenerator
from dev.model.make_model import make_attention_model, alpha_loss
from dev.model.utils import ModelConstants


class Model:
    MODEL_DIR = "../saved_models"

    def __init__(self, model_name=None):
        if model_name is None:
            self.model_name = f"{datetime.now().strftime('%H.%M.%S')}"
            self.model_dir = f"{self.MODEL_DIR}/{self.model_name}"
            self.model = self.__build()
        else:
            self.model_name = model_name
            self.model_dir = f"{self.MODEL_DIR}/{self.model_name}"
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
            "beta_2": 0.98,
        }

        model = make_attention_model(parameters)

        return model

    def __load(self):
        custom_objects = {"alpha_loss": alpha_loss, "RectifiedAdam": RectifiedAdam}
        self.model = load_model(self.model_dir, custom_objects)

    def train(self, x, y, val=None, epochs=ModelConstants.EPOCHS, early_stopping=False, checkpointing=False, **kwargs):
        # Make the training data generator
        train = DataGenerator(x, y, train=True, batch_size=ModelConstants.BATCH_SIZE)

        # Make the validation data generator
        callbacks = []
        if val is not None:
            val = DataGenerator(val[0], val[1], train=False, batch_size=ModelConstants.BATCH_SIZE)

            # Make the early stopping callback
            if early_stopping:
                callbacks.append(EarlyStopping(
                    monitor=ModelConstants.ES_MONITOR,
                    min_delta=ModelConstants.ES_MIN_DELTA,
                    patience=ModelConstants.ES_PATIENCE,
                    restore_best_weights=True
                ))

            # Make the model checkpoint callback
            if checkpointing:
                callbacks.append(ModelCheckpoint(
                    filepath=os.path.join(self.model_dir + "_checkpoint_loss"),
                    monitor="val_loss",
                    save_best_only=True
                ))

                callbacks.append(ModelCheckpoint(
                    filepath=os.path.join(self.model_dir + "_checkpoint_acc"),
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
        self.model.save(self.model_dir)
