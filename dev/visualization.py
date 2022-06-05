import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

from model import Model
from model.utils import Dataset


def plot_calibration_curve(title, y_true, y_pred, n_bins=20):
    from sklearn.calibration import calibration_curve

    y, x = calibration_curve(y_true, y_pred, n_bins=n_bins)
    reg = LinearRegression()
    reg.fit(x[:, np.newaxis], y[:, np.newaxis])

    plt.plot(x, y, 'o', color='red')
    plt.plot(x, reg.predict(x[:, np.newaxis]), '-', color='blue')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('Predicted probability')
    plt.ylabel('Observed frequency')
    plt.title(title)
    plt.show()


def plot_reliability_diagram(model_name, predicted_correctly, argmax, n_bins=20):
    correct_predictions = argmax[predicted_correctly == 1]
    incorrect_predictions = argmax[predicted_correctly == 0]

    binned_correct, bin_edges = np.histogram(correct_predictions, bins=n_bins, range=(0.5, 1))
    binned_incorrect, _ = np.histogram(incorrect_predictions, bins=n_bins, range=(0.5, 1))
    all_bins, _ = np.histogram(argmax, bins=n_bins)

    bin_centers = (bin_edges[1:] + bin_edges[:-1]) / 2
    binned_accuracy = binned_correct / (binned_correct + binned_incorrect)

    reg = LinearRegression()
    reg.fit(bin_centers[:, np.newaxis], binned_accuracy[:, np.newaxis])
    slope = reg.coef_[0][0]
    intercept = reg.intercept_[0]

    # create subplot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    ax1.plot(bin_centers, binned_accuracy, 'o', color='red')  # Data points
    ax1.plot(bin_centers, reg.predict(bin_centers[:, np.newaxis]), '-', color='blue')  # Fitted curve
    ax1.plot([0.5, 1], [0.5, 1], 'k--')  # Perfect calibration line
    ax1.set_xlabel('Predicted Confidence')
    ax1.set_ylabel('Observed Accuracy')
    error = np.mean((bin_centers - reg.predict(bin_centers[:, np.newaxis])) ** 2)
    ax1.title.set_text(f"Slope Error: {error:.2%}")

    ax2.hist([incorrect_predictions, correct_predictions], bins=n_bins, histtype='bar', stacked=True,
             color=["red", "green"])  # Data points
    ax2.set_xlabel('Predicted Confidence')
    ax2.set_ylabel('Count')

    # Calculate the calibration error
    weighted_accuracy = np.sum((all_bins * slope) + intercept) / len(argmax)
    ax2.title.set_text(f"Accuracy: {len(correct_predictions) / len(predicted_correctly):.2%}\n"
                       f"Weighted Accuracy: {weighted_accuracy:.2%}")

    plt.suptitle(f'Reliability diagram for {model_name}')
    plt.show()


def plot_test_data_calibration(model_name):
    # Load the model
    model = Model(model_name)

    # Load test data
    data = Dataset(val_size=0.1)
    x, y_true = data.get_test_data()
    y_pred = model.predict(x)

    # Bin predictions at 0.05 intervals
    predicted_correctly = np.argmax(y_pred, axis=-1) == np.argmax(y_true, axis=-1)
    plot_reliability_diagram(model_name, predicted_correctly, np.max(y_pred, axis=-1))


def plot_recorded_data_calibration(model_name="linear_err"):
    from dev_database_handler import ModelDatabaseHandler

    # Load data from database
    database = ModelDatabaseHandler(model_name)
    records = np.array(database.get_predicted_correctly_and_confidences())
    correctly_predicted, y_pred = records[:, 0], records[:, 1]
    y_pred = (y_pred / 2) + 0.5

    plot_reliability_diagram(model_name, correctly_predicted, y_pred)


def main():
    for model_type in ["before", "after"]:
        plot_test_data_calibration(f"18.08.07_model_{model_type}_temp_scaling")


if __name__ == "__main__":
    main()
