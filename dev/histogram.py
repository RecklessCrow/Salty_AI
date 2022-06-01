import matplotlib.pyplot as plt
import numpy as np
from dev.utils.utils import *
from dev.utils.utils import Model
from scipy.ndimage import gaussian_filter1d

from dev_database_handler import ModelDatabaseHandler

utils = Model("21.18.40_checkpoint_loss")
pred_train = utils.predict(x_test[:100], batch_size=BATCH_SIZE)
pred_test = utils.predict(x_test, batch_size=BATCH_SIZE)
red_confidences = pred_test[:, 0][y_test == [1, 0]]
blue_confidences = pred_test[:, 1][y_test == [0, 1]]
print(pred_test.shape)
red_value = pred_test[:, 0]
prediction[winner == 0] = 1 - prediction[winner == 0]
plt.hist(pred_train, bins=100)
red_confidences = red_value[y_test[:, 0] == 0]
blue_confidences = red_value[y_test[:, 0] == 1]
plt.hist(red_confidences, alpha=0.5, color='red', range=(0, 1), bins=20)
plt.hist(blue_confidences, alpha=0.5, color='blue', range=(0, 1), bins=20)
plt.title("Test matches: Tuned to validation loss")
plt.yscale('log')
plt.show()
mod_rate = lambda count_seen: 1 - ((2 - count_seen) * 0.1)
mods = np.array([mod_rate(count) for count in counts])
mods = mods.reshape(-1, 1)

pred_test = np.clip(((pred_test - 0.5) * mods) + 0.5, 0, 1)
red_win = pred_test[test_y[:1000] == 0]
blue_win = pred_test[test_y[:1000] == 1]

plt.hist(red_win, alpha=0.5, color='red', range=(0, 1), bins=20)
plt.hist(blue_win, alpha=0.5, color='blue', range=(0, 1), bins=20)
plt.title(f"Tuned to val {model_type} (scaled)")
plt.show()
###############################################################################
history = train()
# Plot training & validation accuracy values
print(history.history.keys())
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('utils accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Test'], loc='upper left')
plt.show()
################################################################################
database = ModelDatabaseHandler("linear_err")
confidences = np.array(database.get_confidences())
predicted_correctly = np.array(database.get_predicted_correctly())
print(confidences)

incorrect = confidences[predicted_correctly == 0]
correct = confidences[predicted_correctly == 1]
print(incorrect)

inc_bins, bin_edges, *_ = plt.hist(incorrect, alpha=0.5, color='red', range=(0, 1), bins=10)
cor_bins, *_ = plt.hist(correct, alpha=0.5, color='blue', range=(0, 1), bins=10)
plt.title("Confidence distribution")
plt.legend(['Incorrect', 'Correct'], loc='upper right')
plt.show()

fig, ax1 = plt.subplots()
bin_centers = (bin_edges[1:] + bin_edges[:-1]) / 2

acc = cor_bins / (cor_bins + inc_bins)
ax1.plot(bin_centers, gaussian_filter1d(acc, sigma=2), color='black')
ax1.plot(bin_centers, acc, 'o', color='black')

ax1.set_xlim(0, 1)
ax1.set_ylim(0.5, 1)
ax1.set_xlabel('Confidence')
ax1.set_ylabel('Accuracy')

ax2 = ax1.twinx()
ax2.plot(bin_centers, gaussian_filter1d(inc_bins, sigma=2), '--', color='red')
ax2.plot(bin_centers, gaussian_filter1d(cor_bins, sigma=2), '--', color='blue')
ax2.set_ylabel('Count')

plt.show()
