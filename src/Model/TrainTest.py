import numpy as np
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import StratifiedKFold

from src.DatabaseHandler import DatabaseHandler
from src.Model.Model import Model, TuningModel

database = DatabaseHandler()


def hyperparameter_tuning():
    test_size = 1000
    x, y = database.get_dataset()
    val = x[-test_size:], y[-test_size:]
    x, y = x[:len(x) - test_size], y[:len(y) - test_size]

    model = TuningModel(database.get_num_characters() + 1)
    model.search(x, y, val)


def test_hyperparameter_model():
    test_size = 1000
    x, y = database.get_dataset()
    x_test, y_true = x[-test_size:], y[-test_size:]
    x, y = x[:len(x) - test_size], y[:len(y) - test_size]

    model = Model(database.get_num_characters() + 1)
    model.train(x, y)

    y_pred = model.predict(x_test)
    print(y_pred)
    y_pred = np.around(y_pred)
    print(y_pred)

    print(classification_report(y_true, y_pred))
    # print("Last 10,000")
    # print(classification_report(y_true[-10_000:], y_pred[-10_000:]))
    # print("Last 500")
    # print(classification_report(y_true[-500:], y_pred[-500:]))


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


def train():
    x, y = database.get_dataset()
    model = Model(database.get_num_characters() + 1)
    model.train(x, y)
    model.save()


def main():
    # mode = input("Enter desired run mode:")
    mode = "train"

    if "cross" in mode or "val" in mode:
        cross_validation()
    elif "tune" in mode:
        hyperparameter_tuning()
    elif "test" in mode:
        test_hyperparameter_model()
    else:
        train()


if __name__ == '__main__':
    main()
