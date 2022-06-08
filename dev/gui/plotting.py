import numpy as np
from matplotlib import pyplot as plt

plt.style.use('dark_background')


def slope(point_1: tuple, point_2: tuple):
    """
    Calculates the slope of a line
    :return: Slope
    """
    return (point_2[1] - point_1[1]) / (point_2[0] - point_1[0])


def make_balance_history_plot(balance_history=None):
    """
    Plots the balance history
    :param balance_history: The balance history
    :return: None
    """
    plt.close()

    if balance_history is None:
        # simulate random balance history
        y_values = np.random.randint(low=0, high=100_000, size=10000)
    else:
        y_values = np.array(balance_history).flatten()

    x_values = np.arange(0, len(y_values))

    # Show only the last 25 matches
    x_limit = min(25, len(x_values))

    if len(y_values) > 1:
        # Plot the balance history with colored slopes of the last 25 matches
        for idx in range(len(y_values) - x_limit, len(y_values) - 1):
            slope_value = slope((x_values[idx], y_values[idx]), (x_values[idx + 1], y_values[idx + 1]))
            if slope_value > 0:
                plt.plot(x_values[idx:idx + 2], y_values[idx:idx + 2], color='green')
            else:
                plt.plot(x_values[idx:idx + 2], y_values[idx:idx + 2], color='red')

        # Plot points for each balance
        plt.plot(x_values, y_values, ".", color='white')

        # Plot a trendline
        z = np.polyfit(x_values, y_values, 1)
        p = np.poly1d(z)
        plt.plot(x_values, p(x_values), "--", color='purple', label='Trend')

        plt.xlim(x_values[-x_limit], x_values[-1])

    elif len(y_values) == 1:
        plt.plot(x_values, y_values, ".", color='white')

    # Style the plot
    plt.grid(color='white', linestyle='-', linewidth=0.1)
    plt.xlabel("Match Number")
    plt.ylabel("Balance ($)")
    plt.title("Balance History")
    plt.legend()

    return plt
