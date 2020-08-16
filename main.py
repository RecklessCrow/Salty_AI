import os
import time

import keras
import numpy as np
import data_generator
import train_model
import web_scraper

some_file = os.path.join('checkpoints', '2020-08-15_23-19')


def main():
    # train_model.train(save_to=some_file)

    web_scraper.login()
    my_model = keras.models.load_model(some_file)
    last_red = ''
    last_blue = ''
    while True:
        red, blue = web_scraper.get_reb_blue()
        if red == "" and blue == "":
            continue

        last_red = red
        last_blue = blue

        red_data, blue_data = train_model.encode_input(red, blue)

        if red_data is None or blue_data is None:
            continue

        X = list(red_data)
        X.extend(blue_data)


        probability = my_model.predict()
        predictions = train_model.label_encoder.inverse_transform(probability)
        print(f'{red} vs. {blue}\n'
              f'\tPredicted outcome: {probability} {predictions}')
        winner = ''
        while web_scraper.get_bet_status() is None:
            time.sleep(3)
            winner = web_scraper.get_bet_status()
        print(f'Winner {winner}')


if __name__ == '__main__':
    main()
