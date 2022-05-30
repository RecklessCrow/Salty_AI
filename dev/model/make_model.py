from tensorflow.keras.layers import Input, Dense, Embedding, Flatten, MultiHeadAttention, Dropout, LayerNormalization, \
    StringLookup
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow_addons.optimizers import RectifiedAdam

from dev.model.utils import *


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

    outputs = Dense(units=1)(x)

    model = TF_Model(inputs=inputs, outputs=outputs, name="salty_model")

    model.compile(
        optimizer=RectifiedAdam(
            learning_rate=parameters["learning_rate"],
            epsilon=parameters["epsilon"],
            beta_2=0.98,
            weight_decay=0.01,
            total_steps=STEPS,
            warmup_proportion=0.1,
        ),
        loss=BinaryCrossentropy(
            from_logits=True,
            label_smoothing=parameters["smoothing"],
        ),
        metrics=["accuracy"]
    )

    return model
