import numpy as np
from tqdm import tqdm

from dev_database_handler import SimulationDatabase
from gamblers import GAMBLER_ID_DICT
from model import Model
from simulation.simulated_driver import SaltyBetSim

db = SimulationDatabase()
match_info = db.get_all_match_stats()

model = Model('21.16.57_model_after_temp_scaling')
driver = SaltyBetSim(match_info)

# todo: make this a function
# todo: make the model predict all matches in a single batch to decrease execution time

for gambler_idx in range(len(GAMBLER_ID_DICT)):

    gambler = GAMBLER_ID_DICT[gambler_idx]()

    for idx in tqdm(range(len(match_info)), desc='Simulating Saltybet Matches', unit='matches', ):
        red, blue = driver.get_match()

        if red is None:
            break

        odds = driver.get_odds()
        predicted_odds = model.predict_match(red, blue)
        confidence = np.max(predicted_odds)
        bet_amount = gambler.calculate_bet(confidence, driver)

        pred_idx = np.argmax(predicted_odds)
        predicted_winner = 'red' if pred_idx == 0 else 'blue'
        winner = driver.get_winner()
        predicted_correctly = predicted_winner == winner

        if predicted_correctly:
            large_odds = np.argmax(odds)
            small_odds = np.argmin(odds)

            if pred_idx == large_odds:
                win_amount = bet_amount * (1 / np.max(odds))
            else:
                win_amount = bet_amount * np.max(odds)

            driver.win(win_amount)
        else:
            driver.lose(bet_amount)

    driver.reset()
    print(f'Gambler {gambler_idx} won ${driver.get_balance():,}')
