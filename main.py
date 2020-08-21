import glob
import time
from collections import deque
import numpy as np

import printer
from web_scraper import WebScraper

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf

physical_devices = tf.config.list_physical_devices('GPU')
tf.config.experimental.set_memory_growth(physical_devices[0], True)

STATES = {
    'IDLE': 0,
    'BETS_OPEN': 1,
    'PAYOUT': 2
}
TEAM = {0: 'red', 1: 'blue'}

# Load web scraper
SCRAPER = WebScraper()

# Load model
list_of_files = glob.glob(os.path.join('models', '*'))
MODEL_PATH = max(list_of_files, key=os.path.getctime)
MODEL = tf.keras.models.load_model(MODEL_PATH)


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
    memory_replay = deque(maxlen=10)

    while True:
        current_state = await_next_state(current_state)

        if current_state == STATES['IDLE'] and current_stats is not None:
            info = SCRAPER.get_odds()
            printer.print_idle(info)
            continue

        if current_state == STATES['BETS_OPEN']:
            current_stats = SCRAPER.get_stats()
            prediction = MODEL.predict(current_stats)[0]
            balance = SCRAPER.balance

            predicted_winner = TEAM[np.argmax(prediction)]
            confidence_level = np.max(prediction)

            clip = min(((confidence_level - 0.5) / 1), 1)
            modifier = min(np.arcsin(clip) ** 3, 1)
            bet_amount = int(modifier * balance)

            # Set betting ceiling
            bet_amount = min(1000, bet_amount)

            SCRAPER.bet(bet_amount, predicted_winner)

            info = SCRAPER.get_player_names() + (balance, predicted_winner, confidence_level)
            printer.print_match(info)

            continue

        if current_state == STATES['PAYOUT'] and current_stats is not None:
            payout_message = SCRAPER.status

            if 'blue' in payout_message:    # blue winner
                winner = 'blue'
            elif 'red' in payout_message:   # red winner
                winner = 'red'
            else:                           # tie
                current_stats = None
                continue

            x = current_stats[0]
            y = [1, 0] if winner == 'red' else [0, 1]

            printer.print_payout(winner)

            memory_replay.append((x, y))
            if len(memory_replay) == 10:
                data = np.array([tup[0] for tup in list(memory_replay)])
                labels = np.array([tup[1] for tup in list(memory_replay)])
                MODEL.train_on_batch(data, labels)
                MODEL.save(MODEL_PATH)

            current_stats = None

            continue


if __name__ == '__main__':
    main()
