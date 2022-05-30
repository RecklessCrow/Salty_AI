import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

from tensorflow.keras.activations import sigmoid
from tensorflow.keras.models import load_model
from tensorflow_addons.optimizers import RectifiedAdam


class Model:
    ADAM = RectifiedAdam  # RectifiedAdam optimizer needs to be imported in order to successfully load the model

    def __init__(self, model_name=None):
        """
        Initializes the model by loading the model from the disk given the model name
        :param model_name: the name of the model to load
        """

        self.model_name = model_name
        self.model_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", '..', 'saved_models',
                                       self.model_name)

        if not os.path.exists(self.model_path):
            exit("model file not found!")

        # load in model from parameter
        self.model = load_model(self.model_path)
        self.vocab = self.model.get_layer('string_lookup').get_vocabulary()

    def predict_match(self, red, blue):
        """
        Returns the predicted outcome of a salty bet match given two characters
        :param red: The red character
        :param blue: The blue character
        :return: The predicted outcome of the match. None if both characters are not in the vocabulary
        """

        # check if the characters are in the vocabulary
        if red not in self.vocab and blue not in self.vocab:
            return None

        return sigmoid(self.model.predict([[red, blue]])).numpy()[0][0]
