import os
from shutil import rmtree

import numpy as np
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import StratifiedKFold

from model import Model, TuningModel
from src.database_handler import DatabaseHandler

DATABASE = DatabaseHandler(test_data_is_recent=False, seed=1)


def hyperparameter_tuning(continue_tuning=True):
    """
    Perform hyperparameter tuning through keras hyperparameter tuner
    :return:
    """
    if os.path.isdir("src/model/tuning") and not continue_tuning:
        rmtree("src/model/tuning")

    x, y = DATABASE.get_train_data()
    val = DATABASE.get_val_data()

    model = TuningModel(DATABASE.get_num_characters() + 1)
    model.search(x, y, val)

    rmtree("src/model/tuning")
    # todo: record console output to save hyperparameter tuning results


def cross_validation():
    """
    Run 5-fold cross validation to test effectiveness of model architecture
    :param data:
    :return:
    """
    import numpy as np
    import tensorflow as tf

    x1, y1 = DATABASE.get_train_data()
    x2, y2 = DATABASE.get_val_data()
    x, y = np.concatenate((x1, x2)), np.concatenate((y1, y2))

    del x1, x2, y1, y2

    scores = []

    iterator = StratifiedKFold(n_splits=5, shuffle=True).split(x, y)
    for train_idxs, val_idxs in iterator:
        np.random.seed(1)
        tf.random.set_seed(1)
        model = Model(DATABASE.get_num_characters() + 1)
        x_train, y_train = x[train_idxs], y[train_idxs]
        x_val, y_true = x[val_idxs], y[val_idxs]

        model.train(x_train, y_train, (x_val, y_true))

        y_pred = np.around(model.predict(x_val))

        scores.append(accuracy_score(y_true, y_pred))
        print(classification_report(y_true, y_pred))

    print(f"Model Accuracy: {np.mean(scores):.2%}")


def test_model(filepath=None):
    """
    Test a models' performance over the test set
    :return:
    """
    import tqdm
    x, y = DATABASE.get_train_data()
    val = DATABASE.get_val_data()
    x_test, y_true = DATABASE.get_test_data()

    if filepath:
        model = Model(filepath=filepath)
    else:
        model = Model(DATABASE.get_num_characters() + 1)
        model.train(x, y, val)
        model.save()

    y_pred = model.predict(x_test, batch_size=2 ** 14, verbose=1)

    conf_correct = []
    conf_incorrect = []
    for yp, yt in tqdm.tqdm(zip(y_pred.flatten(), y_true.flatten()), total=len(y_pred)):
        pred = np.around(yp)
        if pred == 0:
            yp = 1 - yp
        conf = (yp - 0.5) * 2

        if pred == yt:
            conf_correct.append(conf)
        else:
            conf_incorrect.append(conf)

    print(
        f"Avg Confidence Correct Predictions:   {np.mean(conf_correct):.2%} +/- {np.std(conf_correct):.2%} ({len(conf_correct):>6})")
    print(
        f"Avg Confidence Incorrect Predictions: {np.mean(conf_incorrect):.2%} +/- {np.std(conf_incorrect):.2%} ({len(conf_incorrect):>6})")
    print(f"Accuracy: {len(conf_correct) / len(y_true):.2%}")
    print(classification_report(y_true, np.around(y_pred)))
    # model.save()


def train(filepath=None):
    """
    Train a model for production
    :param filepath:
    :return:
    """
    x, y = DATABASE.get_dataset()

    if filepath is not None:
        # continue training from a saved model
        model = Model(filepath=filepath)
    else:
        # train a new model
        model = Model(DATABASE.get_num_characters() + 1)

    history = model.train(x, y)
    model.save()

    return history


def main():
    response = input("Select run mode: ")

    if "hyper" in response:
        response = input("Continue from last? y/n: ")
        hyperparameter_tuning(response == "y")
    elif "cross" in response:
        cross_validation()
    elif "test" in response:
        test_model()
    else:
        train()


if __name__ == '__main__':
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    # gpu = input("Use gpu? y/n: ")
    # if gpu == "n":
    #     os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    main()
