import numpy as np
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import StratifiedKFold

from model.model import Model
from model.tuning_model import TuningModel
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
        checkpointing=True,
        early_stopping=False
    )

    # Fit the temperature
    # logits = model.predict(x_test, logits=True)
    # temperature = calculate_temperature(logits, y_test)
    # model.set_temperature(temperature)

    # Test the utils
    y_pred = model.predict(x_test, batch_size=ModelConstants.BATCH_SIZE)
    y_pred = np.argmax(y_pred, axis=-1).reshape(-1, 1)
    report = classification_report(np.argmax(y_test, axis=-1).reshape(-1, 1), y_pred)
    print(report)

    model.save()


def cross_validation():
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
    # Load the data
    dataset = Dataset(val_size=0.1)
    x_train, y_train, = dataset.get_train_data()
    x_val, y_val, = dataset.get_val_data()

    # Initialize and train the utils
    model = TuningModel()
    model.search(x_train, y_train, val=(x_val, y_val), epochs=ModelConstants.EPOCHS)


def train_for_production():
    # Load the data
    dataset = Dataset()
    x, y, = dataset.get_whole_dataset()

    # Initialize and train the utils
    model = Model()
    model.train(x, y, val=None, epochs=ModelConstants.EPOCHS, checkpointing=False, early_stopping=False)
    model.save()


def test_changing_output():
    model = Model()
    model.remove_softmax()
    model.model.summary()
    model.add_temp_layer_and_softmax(10)
    model.model.summary()


def main():
    test_changing_output()

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
