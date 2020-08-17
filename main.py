import os
import time

import keras
import numpy as np

import train_model
import web_scraper

some_file = os.path.join('checkpoints', '2020-08-16_21-01')


# TODO fix busy wait(s)
def main():

    web_scraper.login()
    my_model = keras.models.load_model(some_file)
    last_red = ''
    last_blue = ''

    correct = 0
    matches = 0

    while True:
        red, blue = web_scraper.get_reb_blue()

        if last_red == red and last_blue == blue:
            time.sleep(1)
            continue

        last_red = red
        last_blue = blue

        X = train_model.encode_input(red, blue)

        if None in X:
            print('Character not found.\n')
            continue

        X = [X]
        X = np.array(X).reshape((-1, 2, 8))

        probability = my_model.predict(X)
        prediction = train_model.label_encoder.inverse_transform(probability)[0][0]
        print(f'Red: {red}\n'
              f'Blue: {blue}\n'
              f'Predicted outcome: {prediction} {np.max(probability) * 100:.2f}%')

        winner = None
        while winner is None:
            winner = web_scraper.get_bet_status()
            time.sleep(1)
            pass

        print(f'Winner: {winner}\n')
        matches += 1
        if winner == prediction:
            correct += 1
            print('Correct prediction.')
        else:
            print('Wrong prediction.')
        print(f'Current accuracy {correct / matches * 100:.2f}\n')

        time.sleep(10)


if __name__ == '__main__':
    main()
