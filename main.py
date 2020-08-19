import os
import time
import keras
import numpy as np
import tensorflow as tf
import database_handler
import web_scraper

physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

model_path = os.path.join('models', '2020-08-18_17-27')
np.set_printoptions(precision=2, suppress=True)


# TODO fix busy wait(s)
def main():
    web_scraper.login()
    my_model = keras.models.load_model(model_path)
    prediction_code = {0: 'Red', 1: 'Blue'}

    last_red = ''
    last_blue = ''

    correct = 0
    matches = 0

    while True:
        red, blue = web_scraper.get_red_blue()

        if last_red == red and last_blue == blue:
            time.sleep(1)
            continue

        last_red = red
        last_blue = blue

        put = web_scraper.get_stats()

        probability = my_model.predict(put)[0]
        prediction = prediction_code[np.argmax(probability)]
        probability = np.max(probability)

        print(f'Red: {red}\n'
              f'Blue: {blue}\n'
              f'Predicted outcome: {prediction} {probability:.2%}')

        web_scraper.bet(probability, prediction)

        winner = None
        while winner is None:
            winner = web_scraper.get_bet_status()
            time.sleep(1)

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
