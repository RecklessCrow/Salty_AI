from tensorflow.keras import backend as K

from model.utils import ModelConstants


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
        loss = K.categorical_crossentropy(y_true, y_pred, from_logits=False)

    else:  # Use the alpha loss function
        alpha = K.constant([ModelConstants.ALPHA])
        one = K.constant([1.0])
        loss = (alpha / (alpha - one)) * K.mean(K.sum(y_true * (one - K.pow(y_pred, one - (one / alpha))), axis=-1))

    return loss
