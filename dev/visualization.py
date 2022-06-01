import matplotlib.pyplot as plt
import numpy as np


def plot_pred_histogram(y_true, y_pred, n_bins=20):
    plt.hist(y_pred, bins=n_bins, label='Predicted')
    plt.hist(y_true, bins=n_bins, label='True')
    plt.legend()
    plt.show()


def plot_reliability_diagram(y_true, y_pred, n_bins=10):
    from sklearn.calibration import calibration_curve
    from scipy.ndimage import gaussian_filter1d

    y, x = calibration_curve(y_true, y_pred, n_bins=n_bins)

    plt.plot(x, y, 'o')  # Data points
    plt.plot(x, gaussian_filter1d(y, sigma=2), '-')  # Fitted curve
    plt.plot([0, 1], [0, 1], 'k--')  # Perfect calibration line
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

    plt.title(f'Reliability diagram for test data: {model_name}')
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

    plt.title(f'Reliability diagram for recorded data: {model_name}')
    plot_reliability_diagram(y_true, y_pred)


def main():
    # for model_name in ["21.18.40_checkpoint_loss", "21.18.40_checkpoint_acc", "21.18.40"]:
    #     plot_test_data_calibration(model_name)
    plot_recorded_data_calibration("linear_err")


if __name__ == "__main__":
    main()
