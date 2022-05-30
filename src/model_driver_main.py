import os
import sys
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.activations import sigmoid

from webpage_driver import webpage_handler
from base.base_gambler import Gambler
from model_driver.utils import *
from model_driver import database_handler
from model_driver import salty_bet_driver


def main(model_name: str, gambler: Gambler, user, enyc_pass):
    model = load_model(f'../../saved_models/{model_name}')
    driver = salty_bet_driver.SaltyBetDriver(user, enyc_pass)
    database = database_handler.DatabaseHandler(model_name)
    website_handler = webpage_handler.WebPageHandler(model_name, database.get_balances(),
                                                     database.get_predicted_correctly())

    # initialize variables
    state = STATES["START"]
    betting_balance = None

    while True:
        state = await_next_state(driver, state)

        if state == STATES["BETS_OPEN"]:
            print('BETS_OPEN')

            red, blue = driver.get_fighters()

            if (red, blue) is None:
                confidence = -1
                continue

            red_int, blue_int = encode_character([red, blue])
            print(f'{red} vs {blue}')

            # At least one fighter known
            if not (red_int == 0 and blue_int == 0):
                fighter_vector = np.array([[red_int, blue_int]])
                confidence = model.predict(fighter_vector)[0][0]
                confidence = sigmoid(confidence).numpy()

                predicted_winner = np.around(confidence)

                # Adjust confidence to reflect predicted pred_str as the larger number
                if predicted_winner == 0:
                    confidence = 1 - confidence

                confidence = (confidence - 0.5) * 2
                bet_amount = gambler.calculate_bet(confidence, driver)
                confidence = min(max(confidence, 0.0), 1.0)

            # Both fighters unknown, bet on random team
            else:
                confidence = -1
                continue

            predicted_winner = int_to_team(predicted_winner)
            betting_balance = driver.get_balance()
            driver.bet(max(bet_amount, 1), predicted_winner)

            website_handler.update_page(confidence, predicted_winner,
                    red, blue, bet_amount, odds=None, winner=None)
            continue

        if state == STATES['BETS_CLOSED']:
            if confidence == -1:
                state = STATES['START']
                continue

            print("Bets closed")
            odds = driver.get_odds()
            while odds[0] == 0:
                odds = driver.get_odds()
                time.sleep(1)

            website_handler.update_page(confidence, predicted_winner,
                                        red, blue, bet_amount, odds=odds, winner=None)
            continue

        # Match over
        if state == STATES["PAYOUT"]:
            print('Match over')

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

            database.add_entry(predicted_correctly, confidence, end_balance)
            website_handler.update_page(confidence, predicted_winner,
                                        red, blue, bet_amount, odds=odds, winner=winner, end_balance=end_balance)


def start():
    if len(sys.argv) != 2:
        print("Usage: python3 model_driver_main.py <model_name>")
        sys.exit(1)

    model_name = sys.argv[1]
    model_path = os.path.join("..", "saved_models", model_name)

    if not os.path.exists(model_path):
        print("Model file not found!")
        sys.exit(1)

    from base.base_database_handler import DATABASE
    from base.base_gambler import GAMBLER_ID_DICT

    model_name, gambler_id, user, password = DATABASE.get_model_config_by_name(int(sys.argv[1]))
    gambler = GAMBLER_ID_DICT[gambler_id]

    # todo decrypt password
    main(model_name, gambler, user, password)


if __name__ == '__main__':
    start()
