import matplotlib.pyplot as plt
import numpy as np
from src.Model.expiraments import train
from src.Model.model import Model
import time
from src.database_handler import DatabaseHandler

database = DatabaseHandler(test_data_is_recent=True, seed=1)

train_x, train_y = database.get_train_data()
test_x, test_y = database.get_test_data()

print("Starting")
start_time = time.time()
str_train_x = np.array([f"{r},{b}" for r, b in train_x])
counts = []
for r, b in test_x[:1000]:
    match_up1 = len(str_train_x[str_train_x == f"{r},{b}"])
    match_up2 = len(str_train_x[str_train_x == f"{b},{r}"])
    counts.append(match_up1 + match_up2)

print(f"Finished in {time.time() - start_time} seconds")
counts = np.array(counts)

##################################################################################

model = Model(filepath='./saved_models/model_11.06.20')

# pred_train = model.predict(train_x[:100], batch_size=4096)
pred_test = model.predict(test_x[:1000], batch_size=4096)

# plt.hist(pred_train, bins=100)
red_win  = pred_test[test_y[:1000] == 0]
blue_win = pred_test[test_y[:1000] == 1]

plt.hist(red_win, alpha=0.5, color='red', range=(0, 1), bins=20)
plt.hist(blue_win, alpha=0.5, color='blue', range=(0, 1), bins=20)
plt.show()

mod_rate = lambda count_seen: 1 - ((2 - count_seen) * 0.1)
mods = np.array([mod_rate(count) for count in counts])
mods = mods.reshape(-1, 1)

pred_test = np.clip(((pred_test - 0.5) * mods) + 0.5, 0, 1)
red_win  = pred_test[test_y[:1000] == 0]
blue_win = pred_test[test_y[:1000] == 1]

plt.hist(red_win, alpha=0.5, color='red', range=(0, 1), bins=20)
plt.hist(blue_win, alpha=0.5, color='blue', range=(0, 1), bins=20)
plt.show()


################################################################################

# history = train()
# ## Plot training & validation accuracy values
# print(history.history.keys())
# plt.plot(history.history['accuracy'])
# plt.plot(history.history['val_accuracy'])
# plt.title('Model accuracy')
# plt.ylabel('Accuracy')
# plt.xlabel('Epoch')
# plt.legend(['Train', 'Test'], loc='upper left')
# plt.show()



