# from dev.model.model import Model
# from dev.model.utils import *

# model = Model("21.18.40_checkpoint_loss")

# pred_train = model.predict(x_test[:100], batch_size=BATCH_SIZE)
# pred_test = model.predict(x_test, batch_size=BATCH_SIZE)
# red_confidences = pred_test[:, 0][y_test == [1, 0]]
# blue_confidences = pred_test[:, 1][y_test == [0, 1]]


# print(pred_test.shape)
# red_value = pred_test[:, 0]

# prediction[winner == 0] = 1 - prediction[winner == 0]
# plt.hist(pred_train, bins=100)

# red_confidences = red_value[y_test[:, 0] == 0]
# blue_confidences = red_value[y_test[:, 0] == 1]
# plt.hist(red_confidences, alpha=0.5, color='red', range=(0, 1), bins=20)
# plt.hist(blue_confidences, alpha=0.5, color='blue', range=(0, 1), bins=20)
# plt.title("Test matches: Tuned to validation loss")
# plt.yscale('log')
# plt.show()

# mod_rate = lambda count_seen: 1 - ((2 - count_seen) * 0.1)
# mods = np.array([mod_rate(count) for count in counts])
# mods = mods.reshape(-1, 1)
#
# pred_test = np.clip(((pred_test - 0.5) * mods) + 0.5, 0, 1)
# red_win  = pred_test[test_y[:1000] == 0]
# blue_win = pred_test[test_y[:1000] == 1]
#
# plt.hist(red_win, alpha=0.5, color='red', range=(0, 1), bins=20)
# plt.hist(blue_win, alpha=0.5, color='blue', range=(0, 1), bins=20)
# plt.title(f"Tuned to val {model_type} (scaled)")
# plt.show()


################################################################################

# history = train()
# ## Plot training & validation accuracy values
# print(history.history.keys())
# plt.plot(history.history['accuracy'])
# plt.plot(history.history['val_accuracy'])
# plt.title('model accuracy')
# plt.ylabel('Accuracy')
# plt.xlabel('Epoch')
# plt.legend(['Train', 'Test'], loc='upper left')
# plt.show()
