import numpy as np
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import StratifiedKFold, train_test_split

from src.DatabaseHandler import DatabaseHandler
from src.Model.Model import Model, TuningModel

database = DatabaseHandler()


def hyperparameter_tuning(data):
    x, y = data

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)

    model = TuningModel(database.get_num_characters() + 1)
    model.search(x_train, y_train)


def cross_validation(data):
    """
    Run 5-fold cross validation to test effectiveness of model architecture
    :param data:
    :return:
    """
    x, y = data

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


def main():
    data = database.get_dataset()
    # cross_validation(data)
    hyperparameter_tuning(data)

if __name__ == '__main__':
    main()
