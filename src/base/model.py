import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

from tensorflow.keras.activations import sigmoid
from tensorflow.keras.models import load_model


class Model:
    def __init__(self, model_name=None):
        self.model_name = model_name
        self.model_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", '..', 'saved_models',
                                       self.model_name)

        if not os.path.exists(self.model_path):
            exit("model file not found!")

        # load in model from parameter
        self.model = load_model(self.model_path)

    def predict_match(self, red, blue):
        """
        Returns the predicted outcome of a salty bet match given two characters
        :param red:
        :param blue:
        :return:
        """

        # check if the characters are in the vocabulary
        vocab = self.model.get_layer('string_lookup').get_vocabulary()
        if red not in vocab and blue not in vocab:
            return None

        return sigmoid(self.model.predict([[red, blue]])).numpy()[0][0]
