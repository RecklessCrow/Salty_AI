import time

import numpy as np
from tqdm import tqdm

# from dev_database_handler import SimulationDatabase
from dev.dev_database_handler import SimulationDatabase
from gamblers import GAMBLER_ID_DICT, ExpScaledConfidence2
from model import Model
from dev.simulation.simulated_driver import SaltyBetSim
from skopt import gp_minimize


# todo: make this a function
# todo: make the model predict all matches in a single batch to decrease execution time


def simulate_trial(model, gambler, n_trials):
    money_made = []

    db = SimulationDatabase()
    match_info = db.get_all_match_stats()
    driver = SaltyBetSim(match_info)
    # for trail in tqdm(range(n_trials), desc='Simulating Saltybet Matches', unit='matches', leave=False, ):
    for trail in range(n_trials):

        odds = driver.get_all_odds()
        confidences = driver.predict_on_all_matches(model)
        pred_idx = np.argmax(confidences, axis=-1)

        predicted_winner = np.where(pred_idx == 0, 'red', 'blue')

        winner = driver.get_all_winners()
        predicted_correctly = predicted_winner == winner

        min_odds = np.take_along_axis(odds, np.argmin(confidences, axis=-1)[:, np.newaxis], axis=-1).flatten()
        max_odds = np.take_along_axis(odds, np.argmax(confidences, axis=-1)[:, np.newaxis], axis=-1).flatten()

        win_amount_factor = min_odds / max_odds
        loss_amount_factor = np.ones(confidences.shape[0]) * -1

        factors = np.where(predicted_correctly, win_amount_factor, loss_amount_factor)
        balance = 100
        for match in range(len(odds)):
            match_confidence = max(confidences[match])
            bet_amount = gambler.calculate_bet(match_confidence, driver)
            balance_difference = bet_amount * factors[match]
            balance += balance_difference
            balance = max(balance, 100)
            driver.set_balance(balance)

        money_made.append(balance)
        driver.reset()
        # print(f'Trial {trail + 1}/{n_trials}: Gambler {2} won ${int(balance):,}')

    return money_made


if __name__ == '__main__':
    model_name = "slope_model"
    print(f'Loading model {model_name}')
    model = Model(model_name)
    n_trials = 10


    def f(x):
        gambler = ExpScaledConfidence2(
            confidence_bias_coff=x[0:2],
            ceiling_factor_coff=x[2:4],
            bet_bias_coff=x[4:6],
            aggressive_factor=x[-1])
        money = simulate_trial(model, gambler, n_trials)
        log_money = np.log(money)
        print(f'Average money made: ${np.mean(money):,.0f}')
        print(f'Average log money made: ${np.mean(log_money):,.2f}')
        return -np.mean(log_money)


    res = gp_minimize(
        f,  # the function to minimize
        [(-0.5, -0.25), (15.0, 25.0),
         (-0.5, -0.25), (15.0, 25.0),
         (-0.5, -0.25), (15.0, 25.0),
         (2, 20)],
        acq_func="EI",
        random_state=42)

    print(res.x)
