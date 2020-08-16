import os
import time

import keras

import data_generator
import train_model
import web_scraper

some_file = os.path.join('models', 'my_model')


def main():
    # train_model.train(save_to=some_file)

    web_scraper.login()
    my_model = keras.models.load_model(some_file)
    while True:
        red, blue = web_scraper.get_reb_blue()
        if red == "" and blue == "":
            continue
        X = train_model.encode_input(red, blue)
        probability = my_model.predict(X)
        predictions = train_model.label_encoder.inverse_transform(probability)
        print(f'{red} vs. {blue}\n'
              f'\tPredicted outcome: {probability} {predictions}')
        while web_scraper.get_bet_status() is None:
            time.sleep(3)
            winner = web_scraper.get_bet_status()
        print(winner)


if __name__ == '__main__':
    main()
