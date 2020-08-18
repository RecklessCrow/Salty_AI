import os
import time

import keras
import numpy as np

import database_handler
import train_model
import web_scraper

some_file = os.path.join('models', '2020-08-17_19-19')


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

        if 'Team' in red.split(' ') or 'Team' in blue.split(' '):
            time.sleep(1)
            continue

        if last_red == red and last_blue == blue:
            time.sleep(1)
            continue

        last_red = red
        last_blue = blue

        red_info, blue_info = web_scraper.get_stats()
        database_handler.update_character(red_info)
        database_handler.update_character(blue_info)

        X = database_handler.encode_match(red, blue)

        probability = my_model.predict(X)
        prediction = train_model.label_encoder.inverse_transform(probability)[0][0]
        probability = np.max(probability)
        if prediction:
            prediction = 'Blue'
        else:
            prediction = 'Red'
        print(f'Red: {red}\n'
              f'Blue: {blue}\n'
              f'Predicted outcome: {prediction} {probability:.2%}')

        web_scraper.bet(probability, prediction)

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
        print(f'Current accuracy {correct / matches:.2%}\n')

        w = 1
        if winner == 'Red':
            w = 0

        database_handler.add_match(red, blue, w)
        database_handler.connection.commit()

        time.sleep(5)


if __name__ == '__main__':
    # data_collector()
    main()
