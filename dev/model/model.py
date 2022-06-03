import os
from datetime import datetime

from tensorflow import keras
from tensorflow_addons.optimizers import RectifiedAdam

from dev.model.data_generator import DataGenerator
from dev.model.losses import alpha_loss, joint_loss
from dev.model.make_model import make_attention_model, TempScaling, calculate_temperature
from dev.model.utils import ModelConstants


class Model:
    MODEL_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'saved_models')

    def __init__(self, model_name=None):
        """
        Initialize a model for predicting salty bet matches.
        :param model_name: The name of the model to load. If None, a new model is created.
        """

        if model_name is None:
            model_name = f"{datetime.now().strftime('%H.%M.%S')}"
            self.model_dir = os.path.join(self.MODEL_DIR, model_name)
            self.model = self.__build()

        else:
            self.model_dir = os.path.join(self.MODEL_DIR, model_name)
            assert os.path.exists(self.model_dir), f"Model {model_name} does not exist."
            self.__load()

    @staticmethod
    def __build():
        """
        Build the model.
        """

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
            "loss": joint_loss,  # alpha_loss, joint_loss
        }

        model = make_attention_model(parameters)

        return model

    def rebuild_with_temp(self, x_cal, y_cal):
        """
        Rebuild the model with a temperature scaling layer.
        :param x_cal: The data to calculate the temperature for.
        :param y_cal: The labels to calculate the temperature for.
        :return:
        """
        # Remove the softmax layer to get the logits.
        self.model = keras.models.Model(inputs=self.model.inputs, outputs=self.model.get_layer("logits").output)

        # Calculate the temperature from the calibration data
        logits = self.predict(x_cal)
        temperature = calculate_temperature(logits, y_cal)

        # rebuild model with temperature scaling layer
        new_model = keras.models.Sequential()
        new_model.add(self.model)
        new_model.add(TempScaling(temperature))
        new_model.add(keras.layers.Softmax())
        self.model = new_model

    def train(self, x, y, val=None, epochs=ModelConstants.EPOCHS, batch_size=ModelConstants.BATCH_SIZE,
              early_stopping=False, checkpointing=False, **kwargs):
        """
        Train the model.
        :param x: The training data.
        :param y: The training labels.
        :param val: The validation data.
        :param epochs: The number of epochs to train for.
        :param early_stopping: True if early stopping should be used.
        :param checkpointing: True if checkpointing should be used.
        :param kwargs: Additional arguments to pass to the model for training.
        :return:
        """
        # Make the training data generator
        train = DataGenerator(x, y, train=True, batch_size=batch_size)

        # Make the validation data generator
        callbacks = []
        if val is not None:
            val = DataGenerator(val[0], val[1], train=False, batch_size=batch_size)

            # Make the early stopping callback
            if early_stopping:
                callbacks.append(keras.callbacks.EarlyStopping(
                    monitor=ModelConstants.ES_MONITOR,
                    min_delta=ModelConstants.ES_MIN_DELTA,
                    patience=ModelConstants.ES_PATIENCE,
                    restore_best_weights=True
                ))

            # Make the utils checkpoint callback
            if checkpointing:
                callbacks.append(keras.callbacks.ModelCheckpoint(
                    filepath=os.path.join(self.model_dir + "_checkpoint"),
                    monitor="val_loss",
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

    def predict(self, x, batch_size=ModelConstants.BATCH_SIZE, **kwargs):
        """
        Predict the labels for the given data.
        :param x: The data to predict labels for.
        :param batch_size: The batch size to use.
        :param kwargs: Additional arguments to pass to the model for prediction.
        :return:
        """
        return self.model.predict(x, batch_size=batch_size, **kwargs)

    def save(self, model_name=""):
        """
        Save the model to disk.
        :param model_name: The name of the model to save.
        :return:
        """
        self.model.save(self.model_dir + model_name)

    def __load(self):
        """
        Load a model from disk.
        :return:
        """
        custom_objects = {"alpha_loss": alpha_loss, "RectifiedAdam": RectifiedAdam}
        self.model = keras.models.load_model(self.model_dir, custom_objects)
