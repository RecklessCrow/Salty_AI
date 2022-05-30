import matplotlib.pyplot as plt
import numpy as np
from sklearn.model_selection import train_test_split

from src.base.base_database_handler import DatabaseHandler
from src.experiments.model import Model

SEED = 16

# Create the dataset
model = Model()
model.load("../experiments/saved_models/02.39.02", "model_checkpoint_loss")
db = DatabaseHandler()
matches = np.array(db.get_all_matches())
x, y = matches[:, :-1], matches[:, -1]
del matches
model.tokenizer.fit(x.reshape(-1, 1))
x = model.transform(x).astype(int)
y = (y == "red").astype(int).reshape(-1, 1)

# split data
test_size = 0.2
val_size = 0.1 / (1 - test_size)
train_x, test_x, train_y, test_y = train_test_split(x, y, test_size=test_size, random_state=SEED)
train_x, val_x, train_y, val_y = train_test_split(train_x, train_y, test_size=val_size, random_state=SEED)

# print("Starting")
# start_time = time.time()
# str_train_x = np.array([f"{r},{b}" for r, b in train_x])
# counts = []
# for r, b in test_x[:1000]:
#     match_up1 = len(str_train_x[str_train_x == f"{r},{b}"])
#     match_up2 = len(str_train_x[str_train_x == f"{b},{r}"])
#     counts.append(match_up1 + match_up2)
#
# print(f"Finished in {time.time() - start_time} seconds")
# counts = np.array(counts)

##################################################################################

# pred_train = model.predict(train_x[:100], batch_size=4096)
pred_test = model.predict(test_x, batch_size=4096)

# plt.hist(pred_train, bins=100)
red_win = pred_test[test_y == 0]
blue_win = pred_test[test_y == 1]

plt.hist(red_win, alpha=0.5, color='red', range=(0, 1), bins=20)
plt.hist(blue_win, alpha=0.5, color='blue', range=(0, 1), bins=20)
plt.title("Tuned to val loss")
plt.show()

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



