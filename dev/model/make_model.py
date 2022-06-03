import numpy as np
import tensorflow as tf
from scipy.optimize import minimize
from tensorflow_addons.optimizers import RectifiedAdam

from dev.model.utils import ModelConstants, set_random_state


def make_attention_model(parameters):
    """
    Builds a model with attention
    :param parameters: Dictionary of parameters to use when building the model
    :return: Model
    """
    set_random_state()  # Set random seed for reproducibility

    # Input layer
    inputs = tf.keras.layers.Input(shape=(2,), dtype=tf.string)

    # String to integer encoding
    x = tf.keras.layers.StringLookup(
        mask_token=ModelConstants.UNKNOWN_FIGHTER,
        vocabulary=ModelConstants.VOCAB,
        output_mode='int',
        name='string_lookup'
    )(inputs)

    # Embedding layer
    x = tf.keras.layers.Embedding(
        input_dim=ModelConstants.EMBEDDING_INPUT_DIM,
        output_dim=parameters["embedding_out"],
        mask_zero=True
    )(x)
    x = tf.keras.layers.Dropout(parameters["dropout"])(x)

    # Transformer
    for _ in range(parameters["num_transformers"]):
        # Attention
        sub_x = tf.keras.layers.MultiHeadAttention(
            num_heads=parameters["attention_heads"],
            key_dim=parameters["attention_keys"],
            dropout=parameters["dropout"],
        )(x, x)
        x = tf.keras.layers.LayerNormalization()(x + sub_x)

        # Feed Forward
        sub_x = tf.keras.layers.Dense(
            units=parameters["embedding_out"],
            activation=parameters["ff_activation"]
        )(x)
        sub_x = tf.keras.layers.Dropout(parameters["dropout"])(sub_x)
        x = tf.keras.layers.LayerNormalization()(x + sub_x)

    x = tf.keras.layers.Flatten()(x)

    # Feed forward neural network
    for _ in range(parameters["ff_layers"]):
        x = tf.keras.layers.Dense(
            units=parameters["ff_units"],
            activation=parameters["ff_activation"]
        )(x)
        x = tf.keras.layers.Dropout(parameters["dropout"])(x)

    logits = tf.keras.layers.Dense(units=2, name="logits")(x)
    outputs = tf.keras.layers.Softmax(name="softmax")(logits)

    model = tf.keras.models.Model(inputs=inputs, outputs=outputs, name="salty_model")

    model.compile(
        optimizer=RectifiedAdam(
            learning_rate=parameters["learning_rate"],
            epsilon=parameters["epsilon"],
            beta_2=parameters["beta_2"],
            weight_decay=0.01,
            total_steps=ModelConstants.MAX_TRAINING_STEPS,
            warmup_proportion=0.1,
        ),
        loss=parameters["loss"],
        metrics=["accuracy"]
    )

    return model


def calculate_temperature(logits, y_true):
    """
    Calculate the temperature for model calibration
    :param logits: Logits of the model
    :param y_true: True labels
    :return: Temperature
    """

    def loss(T):
        # Categorical cross entropy loss
        return np.mean(tf.losses.categorical_crossentropy(y_true, logits / T, from_logits=True).numpy())

    res = minimize(loss, x0=np.array(1.0), method='L-BFGS-B', bounds=[(0.0, None)])
    return res.x[0]


@tf.keras.utils.register_keras_serializable()
class TempScaling(tf.keras.layers.Layer):
    def __init__(self, temperature, **kwargs):
        """
        Apply temperature scaling to the logits
        :param temperature: Temperature value
        :param kwargs:
        """
        assert temperature != 0.0, "Temperature cannot be zero"
        self.temperature = temperature
        super(TempScaling, self).__init__(**kwargs)

    def call(self, x):
        return tf.math.divide_no_nan(x, self.temperature)

    def get_config(self):
        config = super().get_config()
        config["temperature"] = self.temperature
        return config

    def compute_output_shape(self, input_shape):
        return None, input_shape
