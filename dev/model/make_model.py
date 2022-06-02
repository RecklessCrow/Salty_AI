import numpy as np
import tensorflow.keras.backend as K
from scipy.optimize import minimize
from tensorflow import string
from tensorflow.keras.layers import Input, Dense, Embedding, Flatten, MultiHeadAttention, Dropout, LayerNormalization, \
    StringLookup
from tensorflow.keras.models import Model as FunctionalModel
from tensorflow_addons.optimizers import RectifiedAdam

from dev.model.utils import ModelConstants, set_random_state


def alpha_loss(y_true, y_pred):
    """
    TF implementation of the alpha loss function
    Supposedly creates a well calibrated model
    from https://arxiv.org/pdf/1906.02314.pdf
    :param y_true:
    :param y_pred:
    :return:
    """

    if ModelConstants.ALPHA == 1.0:  # Use regular cross entropy loss
        loss = K.categorical_crossentropy(y_true, y_pred, from_logits=True)

    else:  # Use the alpha loss function
        y_pred = K.softmax(y_pred)
        alpha = K.constant([ModelConstants.ALPHA])
        one = K.constant([1.0])
        loss = (alpha / (alpha - one)) * K.mean(K.sum(y_true * (one - K.pow(y_pred, one - (one / alpha))), axis=-1))

    return loss


def make_attention_model(parameters):
    """
    model with the transformer architecture
    :param parameters:
    :return:
    """
    set_random_state()

    inputs = Input(shape=(2,), dtype=string)
    x = StringLookup(
        mask_token=ModelConstants.UNKNOWN_FIGHTER,
        vocabulary=ModelConstants.VOCAB,
        output_mode='int',
        name='string_lookup'
    )(inputs)

    x = Embedding(
        input_dim=ModelConstants.EMBEDDING_INPUT_DIM,
        output_dim=parameters["embedding_out"],
        mask_zero=True
    )(x)
    x = Dropout(parameters["dropout"])(x)

    # Transformer
    for _ in range(parameters["num_transformers"]):
        # Attention
        sub_x = MultiHeadAttention(
            num_heads=parameters["attention_heads"],
            key_dim=parameters["attention_keys"],
            dropout=parameters["dropout"],
        )(x, x)
        x = LayerNormalization()(x + sub_x)

        # Feed Forward
        sub_x = Dense(
            units=parameters["embedding_out"],
            activation=parameters["ff_activation"]
        )(x)
        sub_x = Dropout(parameters["dropout"])(sub_x)
        x = LayerNormalization()(x + sub_x)

    x = Flatten()(x)

    # Feed forward neural network
    for _ in range(parameters["ff_layers"]):
        x = Dense(
            units=parameters["ff_units"],
            activation=parameters["ff_activation"]
        )(x)
        x = Dropout(parameters["dropout"])(x)

    outputs = Dense(units=2, name="logits")(x)

    model = FunctionalModel(inputs=inputs, outputs=outputs, name="salty_model")

    model.compile(
        optimizer=RectifiedAdam(
            learning_rate=parameters["learning_rate"],
            epsilon=parameters["epsilon"],
            beta_2=parameters["beta_2"],
            weight_decay=0.01,
            total_steps=ModelConstants.MAX_TRAINING_STEPS,
            warmup_proportion=0.1,
        ),
        loss=alpha_loss,
        metrics=["accuracy"]
    )

    return model


def calculate_temperature(x, y):
    # Optimize T (temperature) using the lbfgs method
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html

    def loss(T):
        # Categorical cross entropy loss
        return np.mean(K.categorical_crossentropy(y, x / T, from_logits=True).numpy())

    res = minimize(loss, x0=np.array(1.0), method='L-BFGS-B', bounds=[(0.0, None)])
    return res.x[0]
