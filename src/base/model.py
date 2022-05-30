import os
import pickle

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import numpy as np
from sklearn.preprocessing import OrdinalEncoder
from tensorflow.keras.activations import sigmoid
from tensorflow.keras.models import load_model

UNKNOWN_CHARACTER = 0



class Model:
    def __init__(self, model_name=None):
        self.model_name = model_name
        self.model_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", '..', 'saved_models', self.model_name)

        if not os.path.exists(self.model_path):
            exit("model file not found!")

        # check if tokenizer exists
        tokenizer_path = os.path.join(self.model_path, "tokenizer.pkl")
        if not os.path.exists(tokenizer_path):
            self.__create_tokenizer()

        self.tokenizer = pickle.load(open(tokenizer_path, "rb"))

        # load in model from parameter
        self.model = load_model(self.model_path)

    def predict_match(self, red, blue):
        """
        Returns the predicted outcome of a salty bet match given two characters
        :param red:
        :param blue:
        :return:
        """
        red = self.transform(red)
        blue = self.transform(blue)

        if not red and not blue:
            return None

        return sigmoid(self.model.predict([[red, blue]])).numpy()[0][0]

    def transform(self, x):
        if isinstance(x, str):
            try:
                return self.tokenizer.transform([[x]])[0][0]
            except ValueError:
                return UNKNOWN_CHARACTER

        return self.tokenizer.transform(x.reshape(-1, 1)).reshape(len(x), 2) + 1

    def __create_tokenizer(self):
        from base.base_database_handler import DATABASE
        characters = DATABASE.get_all_characters()
        tokenizer = OrdinalEncoder()
        tokenizer.fit(np.array(characters).reshape(-1, 1))
        pickle.dump(tokenizer, open(os.path.join(self.model_path, 'tokenizer.pkl'), "wb"))

