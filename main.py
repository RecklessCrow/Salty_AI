import glob
import os
import time
from collections import deque

import numpy as np
import tensorflow as tf

from web_scraper import WebScraper

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

        if current_state == STATES['IDLE']:
            """
            LOG bet_amount potential_gain odds
            """
            continue

        if current_state == STATES['BETS_OPEN']:
            current_stats = SCRAPER.get_stats()
            prediction = MODEL.predict(current_stats)[0]
            balance = SCRAPER.balance

            predicted_winner = np.argmax(prediction)
            confidence_level = np.max(prediction)

            clip = min(((confidence_level - 0.5) / 0.4), 1)
            modifier = min(np.arcsin(clip) ** 1.25, 1)
            bet_amount = int(modifier * balance)

            SCRAPER.bet(bet_amount, TEAM[predicted_winner])

            continue

        if current_state == STATES['PAYOUT'] and current_stats is not None:
            payout_message = SCRAPER.status

            if 'blue' in payout_message:
                winner = 'blue'
            if 'red' in payout_message:
                winner = 'red'

            x = current_stats[0]
            y = [1, 0] if winner == 'red' else [0, 1]

            memory_replay.append((x, y))
            if len(memory_replay) == 10:
                data = np.array([tup[0] for tup in list(memory_replay)])
                labels = np.array([tup[1] for tup in list(memory_replay)])
                MODEL.train_on_batch(data, labels)
                MODEL.save(MODEL_PATH)

            current_stats = None

            """
            GET RESULTS
            LOG RESULTS
            TRAIN MODEL
            """
            continue


if __name__ == '__main__':
    main()
