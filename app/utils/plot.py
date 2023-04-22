import numpy as np
import matplotlib.pyplot as plt

# Confidence values from 0.5 to 1 with 100 equally spaced points
confidence_vals = np.linspace(0.5, 1, 100)

# Calculate the risk values for each confidence value
risk_vals = np.exp(2 * (confidence_vals - 1))

# Plot the risk values against the confidence values
plt.plot(confidence_vals, risk_vals)

# Add labels and a title to the plot
plt.xlabel('Confidence')
plt.ylabel('Risk')
plt.title('Risk vs Confidence')

# Show the plot
plt.show()

# balance_vals = np.logspace(3, 11, num=100, base=10.0)  # Create an array of balance values from 1000 to 100000000000
# max_proportions = []
#
# for balance in balance_vals:
#     max_proportion = 1 / (1 + balance / 10000000)  # Calculate the max proportion using the given formula
#     max_proportions.append(max_proportion)
#
# plt.plot(balance_vals, max_proportions)
# plt.xscale('log')
# plt.xlabel('Balance')
# plt.ylabel('Max Proportion')
# plt.show()
