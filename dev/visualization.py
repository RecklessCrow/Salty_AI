import matplotlib.pyplot as plt
import numpy as np


def plot_pred_histogram(y_true, y_pred, n_bins=20):
    plt.hist(y_pred, bins=10, label='Predicted')
    plt.hist(y_true, bins=10, label='True')
    plt.legend()
    plt.show()


def plot_reliability_diagram(y_true, y_pred, n_bins=10):
    from sklearn.calibration import calibration_curve
    from scipy.ndimage import gaussian_filter1d

    y, x = calibration_curve(y_true, y_pred, n_bins=n_bins)

    plt.plot(x, y, 'o')
    plt.plot(x, gaussian_filter1d(y, sigma=2), '-')
    plt.plot([0, 1], [0, 1], 'k--')
    plt.xlabel('Predicted probability')
    plt.ylabel('Observed probability')
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
    y_pred = model.predict(x)

    # Bin predictions at 0.05 intervals
    y_true = y_true[:, 1]
    y_pred = y_pred[:, 1]

    plt.title('Reliability diagram for test data')
    plot_reliability_diagram(y_true, y_pred)


def plot_recorded_data_calibration(model_name="linear_err"):
    from dev_database_handler import ModelDatabaseHandler

    # Load data from database
    database = ModelDatabaseHandler(model_name)
    records = np.array(database.get_predicted_correctly_and_confidences())
    correctly_predicted, y_pred = records[:, 0], records[:, 1]
    y_true = [
        round(y_pred[i]) if correctly_predicted[i] else round(1 - y_pred[i])
        for i in range(len(correctly_predicted))
    ]

    plt.title('Reliability diagram for recorded data')
    plot_reliability_diagram(y_true, y_pred)


def main():
    # plot_test_data_calibration()
    plot_recorded_data_calibration()


if __name__ == "__main__":
    main()
