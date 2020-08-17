import os
import time

import keras
import numpy as np

import train_model
import web_scraper

some_file = os.path.join('checkpoints', '2020-08-16_02-33')


def main():
    # train_model.train(save_to=some_file)

    web_scraper.login()
    my_model = keras.models.load_model(some_file)
    last_red = ''
    last_blue = ''

    while True:
        red, blue = web_scraper.get_reb_blue()

        if last_red == red and last_blue == blue:
            continue

        last_red = red
        last_blue = blue

        X = train_model.encode_input(red, blue)
        X = [X]
        X = np.array(X)

        if None in X:
            print('Character not found.')
            continue

        probability = my_model.predict(X)
        predictions = train_model.label_encoder.inverse_transform(probability)
        print(f'{red} vs. {blue}\n'
              f'\tPredicted outcome: {predictions[0]} {abs((probability[0][0] * 100) - 50) + 50:.2f}%')

        while web_scraper.get_bet_status() is None:
            pass

        time.sleep(10)


if __name__ == '__main__':
    main()
