from keras_tuner import HyperModel, HyperParameters, Hyperband
from model.utils import *
from tensorflow.python.keras.callbacks import EarlyStopping

from dev.model.data_generator import DataGenerator
from dev.model.make_model import make_attention_model


class TuningModel(HyperModel):
    def __init__(self):
        super().__init__()

    def build(self, hp: HyperParameters):
        hp_dropout = hp.Choice("Dropout", [i * 0.1 for i in range(0, 10)], default=0)  # 0-0.9
        hp_output_dim = hp.Choice("Embedding Outputs", [2 ** p for p in range(2, 9)], default=128)
        hp_transformers = hp.Int("Transformers", min_value=4, max_value=12, default=12)
        hp_heads = hp.Int("Attention Heads", min_value=4, max_value=12, default=12)
        hp_key_dim = hp_heads  # hp.Int("Key Dimention", min_value=4, max_value=12)
        hp_layers = hp.Int("Dense Layers", min_value=1, max_value=4, default=1)
        hp_units = hp.Choice("Dense Units", [2 ** p for p in range(2, 10)], default=64)
        hp_lr = hp.Float("Learning Rate", min_value=0, max_value=5e-3, default=1e-3)
        hp_epsilon = hp.Float("Epsilon", min_value=0, max_value=1e-3, default=1e-7)
        hp_smoothing = hp.Choice("Label Smoothing", [0, 0.01, 0.05, 0.1, 0.15, 0.2], default=0.0)
        hp_activation = hp.Choice("Activation", ["relu", "tanh", "gelu", "selu", "elu", "softplus", "softsign"],
                                  default="relu")

        parameters = {
            "dropout": hp_dropout,
            "embedding_out": hp_output_dim,
            "num_transformers": hp_transformers,
            "attention_heads": hp_heads,
            "attention_keys": hp_key_dim,
            "ff_layers": hp_layers,
            "ff_units": hp_units,
            "learning_rate": hp_lr,
            "epsilon": hp_epsilon,
            "smoothing": hp_smoothing,
            "ff_activation": hp_activation,
        }

        return make_attention_model(parameters)

    def search(self, x, y, val=None, epochs=EPOCHS):
        train = DataGenerator(x, y, train=True, batch_size=BATCH_SIZE)

        tuner = Hyperband(
            self,
            objective=TUNER_OBJECTIVE,
            project_name="tuning",
            factor=FACTOR,
            hyperband_iterations=ITERATIONS,
        )

        early_stopping = EarlyStopping(
            min_delta=ES_MIN_DELTA,
            patience=ES_PATIENCE,
            monitor=ES_MONITOR,
            restore_best_weights=True
        )

        if val is not None:
            val = DataGenerator(val[0], val[1], train=False, batch_size=BATCH_SIZE)

        tuner.search(
            train,
            validation_data=val,
            epochs=epochs,
            callbacks=[early_stopping],
        )
