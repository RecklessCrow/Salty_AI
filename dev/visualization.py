import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression


def plot_pred_histogram(y_true, y_pred, n_bins=20):
    plt.hist(y_pred, bins=n_bins, label='Predicted')
    plt.hist(y_true, bins=n_bins, label='True')
    plt.legend()
    plt.show()


def plot_reliability_diagram(model_name, predicted_correctly, argmax, n_bins=10):
    from sklearn.calibration import calibration_curve
    from scipy.ndimage import gaussian_filter1d

    # y, x = calibration_curve(y_true, y_pred, n_bins=n_bins)

    correct_predictions = argmax[predicted_correctly == 1]
    incorrect_predictions = argmax[predicted_correctly == 0]

    binned_correct, bin_edges = np.histogram(correct_predictions, bins=n_bins)
    binned_incorrect, _ = np.histogram(incorrect_predictions, bins=n_bins)

    bin_centers = (bin_edges[1:] + bin_edges[:-1]) / 2
    binned_accuracy = binned_correct / (binned_correct + binned_incorrect)

    reg = LinearRegression()
    reg.fit(bin_centers[:, np.newaxis], binned_accuracy[:, np.newaxis])
    slope = reg.coef_[0][0]
    intep = reg.intercept_[0]

    # create subplot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    ax1.plot(bin_centers, binned_accuracy, 'o')  # Data points
    ax1.plot(bin_centers, (slope * bin_centers) + intep, '-')  # Fitted curve
    ax1.plot([0.5, 1], [0.5, 1], 'k--')  # Perfect calibration line
    ax1.set_xlabel('Predicted Confidence')
    ax1.set_ylabel('Observed Accuracy')
    ax1.title.set_text(f'Slope: {slope:.2f}')

    ax2.hist([incorrect_predictions, correct_predictions], bins=n_bins, histtype='bar', stacked=True)  # Data points
    # plt.plot(bin_centers, gaussian_filter1d(binned_correct + binned_incorrect, sigma=2), '-')  # Fitted curve
    ax2.set_xlabel('Predicted Confidence')
    ax2.set_ylabel('Count')

    plt.suptitle(f'Reliability diagram for {model_name}')
    plt.show()


def plot_test_data_calibration(model_name="21.18.40_checkpoint_acc"):
    from model.utils import Dataset
    from model.model import Model

    # Load the model
    model = Model(model_name)

    # Load test data
    data = Dataset()
    x, y_true = data.get_test_dataset()

    # Predict
    y_pred = model.predict(x, batch_size=4096)

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

    plt.title(f'Reliability diagram for recorded data: {model_name}')
    plot_reliability_diagram(model_name, correctly_predicted, y_pred)


def main():
    for model_name in ["21.44.38_checkpoint_loss", "22.14.34_checkpoint_loss"]:
        plot_test_data_calibration(model_name)
    # plot_recorded_data_calibration("linear_err")


if __name__ == "__main__":
    main()
