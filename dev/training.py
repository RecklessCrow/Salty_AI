import numpy as np
from sklearn.metrics import accuracy_score

from model.model import Model
from model.utils import Dataset, ModelConstants, SEED


def train_and_evaluate():
    # Load the data
    dataset = Dataset(val_size=0.1)
    x_train, y_train, = dataset.get_train_data()
    x_val, y_val, = dataset.get_val_data()
    x_test, y_test, = dataset.get_test_data()

    # Initialize and train the utils
    model = Model()

    model.train(
        x_train, y_train,
        val=(x_val, y_val),
        epochs=ModelConstants.EPOCHS,
        checkpointing=False,
        early_stopping=False
    )

    model.save('_model_before_temp_scaling')

    model.rebuild_with_temp(x_val, y_val)
    model.save('_model_after_temp_scaling')


def cross_validation():
    from sklearn.model_selection import StratifiedKFold

    dataset = Dataset()
    x, y, = dataset.get_train_data()

    accuracies = []
    iterator = StratifiedKFold(
        n_splits=ModelConstants.CROSS_VALIDATION_FOLDS,
        shuffle=True,
        random_state=SEED
    ).split(x, y)

    for train_idxs, val_idxs in iterator:
        # Define the training and validation data
        x_train, y_train = x[train_idxs], y[train_idxs]
        x_val, y_val = x[val_idxs], y[val_idxs]

        # Initialize and train the utils
        model = Model()
        model.train(
            x_train, y_train,
            val=(x_val, y_val),
            epochs=ModelConstants.EPOCHS,
            checkpointing=False,
            early_stopping=False
        )

        # Test the utils
        y_pred = np.argmax(model.predict(x_val))
        y_true = np.argmax(y_val)
        accuracy = accuracy_score(y_true, y_pred)
        print(f"Accuracy: {accuracy:.2f%}")

    # Print the average accuracy over all buckets
    print(f"Average accuracy: {np.mean(accuracies):.2f%} +/- {np.std(accuracies):.2f%}")


def hyper_parameter_tuning():
    from model.tuning_model import TuningModel

    # Load the data
    dataset = Dataset(val_size=0.1)
    x_train, y_train, = dataset.get_train_data()
    x_val, y_val, = dataset.get_val_data()

    # Initialize and train the utils
    model = TuningModel()
    model.search(x_train, y_train, val=(x_val, y_val), epochs=ModelConstants.EPOCHS)


def train_for_production(use_temp_scaling=False):
    # Load the data
    dataset = Dataset(test_size=0.1)
    x_train, y_train, = dataset.get_train_data()
    x_cal, y_cal = dataset.get_test_data()

    model = Model()
    model.train(x_train, y_train, epochs=ModelConstants.EPOCHS, checkpointing=False, early_stopping=False)

    if use_temp_scaling:
        model.rebuild_with_temp(x_cal, y_cal)

    model.save()


def main():
    # Get user input for run mode
    while True:
        mode = input("Enter 'train' to train the utils, 'cv' to cross validate the utils, 'tuning' to tune the utils, "
                     "or 'prod' to train the utils for production: ")

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
