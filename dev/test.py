from src.base.model import Model

model = Model('../saved_models/07.24.40/model_checkpoint_acc')
out = model.predict_match("a", "b")
