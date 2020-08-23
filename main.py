import glob
import os
import time

import numpy as np

import database_handler
import utils
from utils import Memory, label_encoder
from web_scraper import WebScraper

STATES = {
    'IDLE': 0,
    'BETS_OPEN': 1,
    'PAYOUT': 2
}
TEAM = {1: 'red', 0: 'blue'}

# Load web scraper
SCRAPER = WebScraper()

# Load model
list_of_files = glob.glob(os.path.join('models', '*'))
MODEL_PATH = max(list_of_files, key=os.path.getctime)


def decode_state(encoded_state):
    if 'locked' in encoded_state:
        return STATES['IDLE']
    if 'open' in encoded_state:
        return STATES['BETS_OPEN']
    if 'payout' in encoded_state:
        return STATES['PAYOUT']
    return STATES["IDLE"]


def await_next_state(last_state):
    state = last_state
    while state == last_state:
        state = decode_state(SCRAPER.status)
        time.sleep(1)

    return state


def main():
    current_state = STATES['IDLE']
    current_stats = None
    # memory_replay = Memory()

    while True:
        current_state = await_next_state(current_state)

        if current_state == STATES['IDLE'] and current_stats is not None:
            info = SCRAPER.get_odds()
            utils.print_idle(info)
            continue

        if current_state == STATES['BETS_OPEN']:
            current_stats = SCRAPER.get_stats()
            prediction = MODEL.predict(current_stats)[0]
            balance = SCRAPER.balance

            predicted_winner = TEAM[np.argmax(prediction)]
            confidence_level = np.max(prediction)

            clip = (confidence_level - 0.5) * 2
            modifier = (.1 * (11 ** clip)) - .1
            inv_modifier = max(.999999**balance, .1)
            modifier = inv_modifier * modifier
            bet_amount = balance * modifier

            if balance < 100_000:
                bet_amount = balance * confidence_level // 2
            if balance < 10_000:
                bet_amount = balance

            SCRAPER.bet(int(bet_amount), predicted_winner)

            info = SCRAPER.get_player_names() + (balance, predicted_winner, confidence_level)
            utils.print_match(info)

            continue

        if current_state == STATES['PAYOUT'] and current_stats is not None:
            payout_message = SCRAPER.status

            red, blue = SCRAPER.get_player_names()

            if 'blue' in payout_message:    # blue winner
                winner = 'blue'
            elif 'red' in payout_message:   # red winner
                winner = 'red'
            else:                           # tie
                current_stats = None
                continue

            utils.print_payout(winner)

            database_handler.add_match(red, blue, winner)

            x = current_stats
            y = [[1, 0]] if winner == 'red' else [[0, 1]]
            data = np.array(x)
            labels = np.array(y)
            # Memory.add_memory(x, y)
            # data, labels = Memory.get_memories()
            MODEL.train_on_batch(data, labels)
            MODEL.save(MODEL_PATH)

            current_stats = None

            continue


if __name__ == '__main__':

    # Remove excessive tf messages
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    import tensorflow as tf

    # fix tf for my computer
    physical_devices = tf.config.list_physical_devices('GPU')
    tf.config.experimental.set_memory_growth(physical_devices[0], True)

    # load model
    MODEL = tf.keras.models.load_model(MODEL_PATH)
    tf.keras.backend.set_value(MODEL.optimizer.learning_rate, 0.00001)
    main()
