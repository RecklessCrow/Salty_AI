import tensorflow.keras.backend as K
from tensorflow.keras.layers import Input, Dense, Embedding, Flatten, MultiHeadAttention, Dropout, LayerNormalization, \
    StringLookup
from tensorflow.keras.models import Model as KerasModel
from tensorflow.python.ops.gen_nn_ops import softmax
from tensorflow_addons.optimizers import RectifiedAdam

from dev.model.utils import *


def alpha_loss(y_true, y_pred):
    """
    TF implementation of the alpha loss function
    :param y_true:
    :param y_pred:
    :return:
    """
    y_true = tf.convert_to_tensor(y_true)
    y_pred = tf.convert_to_tensor(y_pred)
    y_pred = softmax(y_pred)
    # y_pred = tf.clip_by_value(y_pred, K.epsilon(), 1. - K.epsilon())

    my_alpha = 4.0

    if my_alpha == 1.0:  # standard binary cross entropy
        loss = K.mean(K.sum(-y_true * K.log(y_pred + K.epsilon()), axis=-1))

    else:  # weighted binary cross entropy
        alpha = tf.constant([my_alpha])
        one = tf.constant([1.0])
        loss = (alpha / (alpha - one)) * K.mean(K.sum(y_true * (one - K.pow(y_pred, one - (one / alpha))), axis=-1))

    return loss


def make_attention_model(parameters):
    """
    model with the transformer architecture
    :param parameters:
    :return:
    """
    set_random_state()

    inputs = Input(shape=(2,), dtype=tf.string)
    x = StringLookup(
        mask_token=UNKNOWN_FIGHTER,
        vocabulary=VOCAB,
        output_mode='int',
        name='string_lookup'
    )(inputs)

    x = Embedding(input_dim=len(VOCAB) + 1, output_dim=parameters["embedding_out"], mask_zero=True)(x)
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

    outputs = Dense(units=2)(x)

    model = KerasModel(inputs=inputs, outputs=outputs, name="salty_model")

    model.compile(
        optimizer=RectifiedAdam(
            learning_rate=parameters["learning_rate"],
            epsilon=parameters["epsilon"],
            beta_2=0.98,
            weight_decay=0.01,
            total_steps=MAX_TRAINING_STEPS,
            warmup_proportion=0.1,
        ),
        # loss=BinaryCrossentropy(
        #     from_logits=True,
        #     label_smoothing=parameters["smoothing"],
        # ),
        loss=alpha_loss,
        metrics=["accuracy"]
    )

    return model
