import numpy as np
from sklearn.model_selection import train_test_split

from src.base_database_handler import DatabaseHandler
from src.expiraments.model import TuningModel

SEED = 4

db = DatabaseHandler()
characters = db.get_all_characters()
model = TuningModel(characters)

matches = np.array(db.get_all_matches())
x, y = matches[:, :-1], matches[:, -1]
del matches
x = model.transform(x)
y = (y == "red").astype(int).reshape(-1, 1)

test_size = 0.2
val_size = 0.1 / (1 - test_size)
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=test_size, random_state=SEED)
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, test_size=val_size, random_state=SEED)

model.search(x_train, y_train, val=(x_val, y_val), epochs=100)
