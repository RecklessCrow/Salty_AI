import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import tensorflow as tf


class Model:
    MODEL_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'saved_models')
    UNKNOWN_FIGHTER = '<unknown>'

    def __init__(self, model_name=None):
        """
        Initializes the model by loading the model from the disk given the model name
        :param model_name: the name of the model to load
        """

        self.model_path = os.path.join(self.MODEL_DIR, model_name)
        self.model_name = model_name

        assert os.path.exists(self.model_path), f"Model {model_name} does not exist."

        # load in model from parameter
        self.model = tf.keras.models.load_model(self.model_path, compile=False)
        self.vocab = self.model.get_layer('string_lookup').get_vocabulary()

    def predict_match(self, red, blue):
        """
        Returns the predicted outcome of a salty bet match given two characters
        :param red: The red character
        :param blue: The blue character
        :return: The predicted outcome of the match. None if both characters are not in the vocabulary
        """

        # Check if the characters are in the vocabulary
        if red not in self.vocab:
            red = self.UNKNOWN_FIGHTER
        if blue not in self.vocab:
            blue = self.UNKNOWN_FIGHTER

        # If both characters are not in the vocabulary, cannot make a prediction
        if red == self.UNKNOWN_FIGHTER and blue == self.UNKNOWN_FIGHTER:
            return None

        prediction = self.model.predict([[red, blue]], verbose=0)
        return prediction[0]

    def predict_batch(self, batch):
        """
        Returns the predicted outcomes of a batch of salty bet matches
        :param batch: A list of tuples containing the characters of the red and blue fighters
        :return: A list of the predicted outcomes of the matches
        """
        return self.model.predict(batch, verbose=0)
