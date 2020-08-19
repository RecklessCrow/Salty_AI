import os
import time

import keras
import numpy as np
import tensorflow as tf

import database_handler
import web_scraper
from logger_script import logger

# fix tf
physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# limit np printing
np.set_printoptions(precision=2, suppress=True)

# get model
model_path = os.path.join('models', '2020-08-19_16-23')


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

        balance = web_scraper.get_balance()
        web_scraper.bet(probability, prediction)

        # Log initial data
        log_str = f'{red} vs. {blue}\n' \
                  f'Predicted outcome: {prediction} | {probability:>6.2%}\n' \
                  f'Current balance: ${balance:,}'
        logger.info(log_str)
        print(log_str)

        # todo
        #  determine if match was upset (greater than 2 : 1 odds)

        # Log betting data
        # todo find better way of waiting until data is available
        time.sleep(60)
        bet_amount, potential_gain, red_odds, blue_odds = web_scraper.get_odds()
        log_str = f'Odds: {red_odds} : {blue_odds}\n' \
                  f'Potential upset: {red_odds > 2 or blue_odds > 2}\n' \
                  f'Bet upset: {red_odds == 1 and prediction == "Red" or blue_odds == 1 and prediction == "Blue"}\n' \
                  f'Bet: ${bet_amount:,} -> ${potential_gain:,}\n' \
                  f'Percent of balance bet: {bet_amount / balance:>6.2%}\n'
        logger.info(log_str)
        print(log_str)

        # todo find better way to wait until a winner is decided
        winner = None
        while winner is None:
            winner = web_scraper.get_bet_status()
            time.sleep(1)

        old_balance = balance
        balance = web_scraper.get_balance()
        payout = old_balance - balance
        if payout < 0:
            payout = f'-${payout:,}'
        else:
            payout = f'${payout:,}'

        # Log winner and payouts
        log_str = f'Winner: {winner}\n' \
                  f'Payout: {payout}'
        logger.info(log_str)
        print(log_str)

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
