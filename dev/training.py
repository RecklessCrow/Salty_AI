import numpy as np
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import StratifiedKFold

from dev.model.tuning_model import TuningModel
from dev.model.utils import Dataset, ModelConstants, SEED
from model.model import Model


def train_and_evaluate():
    # Load the data
    dataset = Dataset(make_val=True)
    x_train, y_train, = dataset.get_train_dataset()
    x_val, y_val, = dataset.get_val_dataset()
    x_test, y_test, = dataset.get_test_dataset()

    # Initialize and train the model
    model = Model()
    model.train(
        x_train, y_train,
        val=(x_val, y_val),
        epochs=ModelConstants.EPOCHS,
        checkpointing=True,
        early_stopping=False
    )
    model.save()

    # Test the model
    y_pred = model.predict(x_test, batch_size=ModelConstants.BATCH_SIZE)
    y_pred = np.argmax(y_pred, axis=-1).reshape(-1, 1)
    report = classification_report(np.argmax(y_test, axis=-1).reshape(-1, 1), y_pred)
    print(report)


def cross_validation():
    dataset = Dataset(make_val=False)
    x, y, = dataset.get_train_dataset()

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

        # Initialize and train the model
        model = Model()
        model.train(
            x_train, y_train,
            val=(x_val, y_val),
            epochs=ModelConstants.EPOCHS,
            checkpointing=False,
            early_stopping=False
        )

        # Test the model
        y_pred = np.argmax(model.predict(x_val))
        y_true = np.argmax(y_val)
        accuracy = accuracy_score(y_true, y_pred)
        print(f"Accuracy: {accuracy:.2f%}")

    # Print the average accuracy over all buckets
    print(f"Average accuracy: {np.mean(accuracies):.2f%} +/- {np.std(accuracies):.2f%}")


def hyper_parameter_tuning():
    # Load the data
    dataset = Dataset(make_val=True)
    x_train, y_train, = dataset.get_train_dataset()
    x_val, y_val, = dataset.get_val_dataset()

    # Initialize and train the model
    model = TuningModel()
    model.search(x_train, y_train, val=(x_val, y_val), epochs=ModelConstants.EPOCHS)


def train_for_production():
    # Load the data
    dataset = Dataset()
    x, y, = dataset.get_all_dataset()

    # Initialize and train the model
    model = Model()
    model.train(x, y, val=None, epochs=ModelConstants.EPOCHS, checkpointing=False, early_stopping=False)
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
