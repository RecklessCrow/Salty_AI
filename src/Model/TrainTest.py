from shutil import rmtree

import numpy as np
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import StratifiedKFold

from src.DatabaseHandler import DatabaseHandler
from src.Model.Model import Model, TuningModel

database = DatabaseHandler(add_mirrored_matches=False)


def hyperparameter_tuning():
    x, y = database.get_train_data()
    val = database.get_val_data()

    model = TuningModel(database.get_num_characters() + 1)
    model.search(x, y, val)

    rmtree("src/Model/parameters")
    # todo: record console output to save hyperparameter tuning results


def test_hyperparameter_model():
    x, y = database.get_train_data()
    val = database.get_val_data()
    x_test, y_true = database.get_test_data()

    model = Model(database.get_num_characters() + 1)
    model.train(x, y, val)

    y_pred = model.predict(x_test)
    y_pred = np.around(y_pred)

    print(classification_report(y_true, y_pred))


def cross_validation():
    """
    Run 5-fold cross validation to test effectiveness of model architecture
    :param data:
    :return:
    """

    x, y = database.get_dataset()

    scores = []

    iterator = StratifiedKFold(n_splits=5, shuffle=True).split(x, y)
    for train_idxs, val_idxs in iterator:
        model = Model(database.get_num_characters() + 1)
        train_x, train_y = x[train_idxs], y[train_idxs]
        val_x, y_true = x[val_idxs], y[val_idxs]

        model.train(train_x, train_y)

        y_pred = np.around(model.predict(val_x))

        scores.append(accuracy_score(y_true, y_pred))
        print(classification_report(y_true, y_pred))

    print(f"Model Accuracy: {np.mean(scores):.2%}")


def train(filepath=None):
    x, y = database.get_dataset()
    if filepath is not None:
        model = Model(filepath=filepath)
    else:
        model = Model(database.get_num_characters() + 1)
    model.train(x, y)
    model.save()


def main():
    # mode = input("Enter desired run mode:")
    hyperparameter_tuning()


if __name__ == '__main__':
    main()
