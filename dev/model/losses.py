import tensorflow as tf

from model.utils import ModelConstants


def alpha_loss(y_true, y_pred):
    """
    TF implementation of the alpha loss function
    Supposedly creates a well calibrated model
    from https://arxiv.org/pdf/1906.02314.pdf
    :param y_true: ground truth
    :param y_pred: predictions
    :return: loss
    """

    if ModelConstants.ALPHA == 1.0:  # Use regular cross entropy loss
        loss = tf.losses.categorical_crossentropy(y_true, y_pred, from_logits=False)

    else:  # Use the alpha loss function
        alpha = tf.constant([ModelConstants.ALPHA])
        one = tf.constant([1.0])
        loss = (alpha / (alpha - one)) * tf.math.reduce_mean(
            tf.math.reduce_sum(y_true * (one - tf.math.pow(y_pred, one - (one / alpha))), axis=-1))

    return loss


def get_slope(y_true, y_pred):
    """
    Calculates the slope of the expected calibration curve
    :param y_true: ground truth
    :param y_pred: predictions
    :return: loss
    """

    n_bins = 10

    # y_pred = K.softmax(y_pred)
    winner_label = tf.math.argmax(y_true, axis=1)
    argmaxes = tf.math.argmax(y_pred, axis=1)
    y_pred_max = tf.math.reduce_max(y_pred, axis=1)

    all_idx = tf.histogram_fixed_width_bins(
        y_pred_max,
        [0.55, 0.95],
        nbins=n_bins
    )

    correct_idx = all_idx[argmaxes == winner_label]
    incorrect_idx = all_idx[argmaxes != winner_label]

    correct_bin_amounts = tf.math.bincount(correct_idx, minlength=n_bins)
    incorrect_bin_amounts = tf.math.bincount(incorrect_idx, minlength=n_bins)

    binned_acc = tf.math.divide_no_nan(tf.cast(correct_bin_amounts, tf.float32),
                                       tf.cast(correct_bin_amounts + incorrect_bin_amounts, tf.float32))

    diffs = tf.experimental.numpy.diff(binned_acc) * (1.0 / 0.05)
    slope = tf.math.reduce_mean(diffs)

    return slope


def joint_loss(y_true, y_pred):
    """
    Combines (alpha loss / categorical cross entropy loss) with the slope loss
    :param y_true: ground truth
    :param y_pred: predictions
    :return: loss
    """

    # weighted_acc_loss = get_weighted_acc(y_true, y_pred)
    # weighted_acc_loss = (1 - weighted_acc_loss) * 3
    slope_loss = get_slope(y_true, y_pred)
    slope_loss = abs(1 - slope_loss) * 3
    loss = alpha_loss(y_true, y_pred)
    return loss + slope_loss
