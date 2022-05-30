from model.model import Model
from model.utils import *

model = Model()
model.model.summery()
model.train(x_train, y_train, val=(x_val, y_val), epochs=EPOCHS, checkpointing=False, early_stopping=False)
model.save()
