import time

import numpy as np
from tqdm import tqdm

from dev_database_handler import SimulationDatabase
from gamblers import GAMBLER_ID_DICT
from model import Model
from simulation.simulated_driver import SaltyBetSim

db = SimulationDatabase()
match_info = db.get_all_match_stats()
matchups = np.array(match_info)[:, 0:2]

model = Model('slope_model')
driver = SaltyBetSim(match_info)

# todo: make this a function
# todo: make the model predict all matches in a single batch to decrease execution time

# for gambler_idx in range(len(GAMBLER_ID_DICT)):

gambler = GAMBLER_ID_DICT[2]()
predicted_odds = model.predict_batch(matchups)

for idx in tqdm(range(len(match_info)), desc='Simulating Saltybet Matches', unit='matches', ):
    red, blue = driver.get_match()

    if red is None:
        break

    odds = driver.get_odds()
    confidence = np.max(predicted_odds[idx])
    bet_amount = gambler.calculate_bet(confidence, driver)

    pred_idx = np.argmax(predicted_odds[idx])
    predicted_winner = 'red' if pred_idx == 0 else 'blue'
    winner = driver.get_winner()
    predicted_correctly = predicted_winner == winner

    if predicted_correctly:
        if pred_idx == np.argmax(odds):  # Bet on the favored team
            win_amount = bet_amount * (1 / np.max(odds))
        else:  # Bet on the underdog (Upset)
            win_amount = bet_amount * np.max(odds)

        driver.win(win_amount)

    else:
        driver.lose(bet_amount)

print(f'Gambler {2} won ${driver.get_balance():,}')
driver.reset()
time.sleep(1)
