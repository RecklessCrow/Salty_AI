from keras_tuner import HyperModel, HyperParameters, Hyperband
from tensorflow.python.keras.callbacks import EarlyStopping

from dev.model.data_generator import DataGenerator
from dev.model.make_model import make_attention_model
from utils import *


class TuningModel(HyperModel):
    def __init__(self):
        super().__init__()

    def build(self, hp: HyperParameters):
        hp_dropout = hp.Choice("Dropout", [eval(f"0.{x}") for x in range(1, 10)])  # 0.1-0.9
        hp_output_dim = hp.Choice("Embedding Outputs", [2 ** p for p in range(2, 10)])
        hp_transformers = 12  # hp.Int("Transformers", min_value=8, max_value=16)
        hp_heads = 12  # hp.Int("Attention Heads", min_value=4, max_value=12)
        hp_key_dim = 12  # hp.Int("Key Dimention", min_value=4, max_value=12)
        hp_layers = hp.Int("Dense Layers", min_value=1, max_value=4)
        hp_units = hp.Choice("Dense Units", [2 ** p for p in range(2, 10)])
        hp_lr = hp.Float("Learning Rate", min_value=0, max_value=1e-3)
        hp_epsilon = hp.Float("epsilon", min_value=0, max_value=1e-3)
        hp_smoothing = hp.Float("Label Smoothing", min_value=0, max_value=0.2)

        parameters = {
            "dropout": hp_dropout,
            "embedding_out": hp_output_dim,
            "num_transformers": hp_transformers,
            "attention_heads": hp_heads,
            "attention_keys": hp_key_dim,
            "ff_layers": hp_layers,
            "ff_units": hp_units,
            "ff_activation": "gelu",
            "learning_rate": hp_lr,
            "epsilon": hp_epsilon,
            "smoothing": hp_smoothing,
        }

        return make_attention_model(parameters)

    def search(self, x, y, val=None, epochs=EPOCHS):
        import math
        iterations = 10
        factor = 10
        total_epochs = epochs * (math.log(epochs, factor) ** 2) * iterations
        print(total_epochs)

        train = DataGenerator(x, y, train=True, batch_size=BATCH_SIZE)

        tuner = Hyperband(
            self,
            objective=TUNER_OBJECTIVE,
            project_name="tuning",
            factor=factor,
            hyperband_iterations=iterations,
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
