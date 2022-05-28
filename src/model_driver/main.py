import sys

import numpy as np

import salty_bet_driver
from src.base_gambler import Gambler
from src.experiments.model import Model
from src.model_driver.database_handler import DatabaseHandler
from utils import *


def main(model_name: str, gambler: Gambler, user, enyc_pass):
    # Initialize
    driver = salty_bet_driver.SaltyBetDriver(user, enyc_pass)
    model = Model(f'../../saved_models/{model_name}/')
    model_database = DatabaseHandler(model_name)

    state = STATES["START"]
    betting_balance = None
    confidence = None
    predicted_winner = None

    while True:
        state = await_next_state(driver, state)

        if state == STATES["BETS_OPEN"]:

            red, blue = driver.get_fighters()

            if (red, blue) is None:
                continue

            confidence = model.predict([red, blue])

            # At least one fighter known
            if confidence:
                predicted_winner = np.around(confidence)

                # Adjust confidence to reflect predicted team as the larger number
                if predicted_winner == 0:
                    confidence = 1 - confidence

                bet_amount = gambler.calculate_bet(confidence, driver)

            # Both fighters unknown, todo define behavior
            else:
                continue

            predicted_winner = int_to_team(predicted_winner)
            betting_balance = driver.get_balance()
            driver.bet(max(bet_amount, 1), predicted_winner)

            # todo - update model's webpage with fighters and confidence and betting amount
            continue

        if state == STATES['BETS_CLOSED']:
            # todo - update model's webpage with odds and awards
            continue

        # Match over
        if state == STATES["PAYOUT"]:

            payout_message = driver.get_game_state()

            if "red" in payout_message:  # red winner
                winner = "red"
            elif "blue" in payout_message:  # blue winner
                winner = "blue"
            else:  # tie
                continue

            end_balance = driver.get_balance()
            winnings = end_balance - betting_balance
            predicted_correctly = winner == predicted_winner

            model_database.add_entry(predicted_correctly, confidence, end_balance)
            # todo create feed panel with results


def arg_handler():
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <model_path>")
        sys.exit(1)

    assert sys.argv[1].isnumeric()

    from src.base_database_handler import DATABASE
    from src.base_gambler import GAMBLER_ID_DICT

    model_name, gambler_id, user, password = DATABASE.get_model_config_by_id(int(sys.argv[1]))
    gambler = GAMBLER_ID_DICT[gambler_id]

    # todo decrypt password
    main(model_name, gambler, user, password)


if __name__ == '__main__':
    arg_handler()
