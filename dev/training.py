from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import StratifiedKFold

from dev.model.tuning_model import TuningModel
from dev.model.utils import *
from dev.model.utils import y_test
from model.model import Model


def train_and_evaluate():
    # initialize the model
    model = Model()
    model.train(x_train, y_train, val=(x_val, y_val), epochs=EPOCHS, checkpointing=True, early_stopping=False)
    model.save()

    # test
    y_pred = model.predict(x_test, batch_size=BATCH_SIZE)
    y_pred = np.argmax(y_pred, axis=-1).reshape(-1, 1)
    report = classification_report(np.argmax(y_test, axis=-1).reshape(-1, 1), y_pred)
    print(report)


def cross_validation():
    accuracies = []
    iterator = StratifiedKFold(n_splits=BUCKETS, shuffle=True, random_state=SEED).split(x, y)
    for train_idxs, val_idxs in iterator:
        x_train, y_train = x[train_idxs], y[train_idxs]
        x_val, y_val = x[val_idxs], y[val_idxs]
        model = Model()
        model.train(x_train, y_train, val=(x_val, y_val), epochs=EPOCHS, checkpointing=False, early_stopping=False)
        y_pred = model.predict(x_test)
        accuracy = accuracy_score(y_test, y_pred)
        accuracies.append(accuracy)
        print("Accuracy: %.2f%%" % (accuracy * 100))

    print("Mean accuracy: %.2f%%" % (np.mean(accuracies) * 100))
    print("Standard deviation: %.2f%%" % (np.std(accuracies) * 100))


def hyper_parameter_tuning():
    model = TuningModel()
    model.search(x_train, y_train, val=(x_val, y_val), epochs=EPOCHS)


def train_for_production():
    model = Model()
    model.train(x, y, val=None, epochs=EPOCHS, checkpointing=False, early_stopping=False)
    model.save()


def main():
    # Get user input for run mode
    while True:
        mode = input("Enter 'train' to train the model, 'cv' to cross validate the model, 'tuning' to tune the model, "
                     "or 'prod' to train the model for production: ")

        if mode == "train":
            train_and_evaluate()
            break
        elif mode == "cv":
            cross_validation()
            break
        elif mode == "tuning":
            hyper_parameter_tuning()
            break
        elif mode == "prod":
            train_for_production()
            break
        else:
            print("Invalid input.")


if __name__ == '__main__':
    main()
