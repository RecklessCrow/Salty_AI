import json
import os
import sys

import numpy as np

from base.base_gambler import Gambler
from base.model import Model
from model_utils import database_handler, salty_bet_driver
from model_utils.utils import *
from web_utils import webpage_handler


def main(model_name: str, gambler: Gambler, user, enyc_pass):
    model = Model(model_name)
    driver = salty_bet_driver.SaltyBetDriver(user, enyc_pass)
    model_database = database_handler.DatabaseHandler(model_name)
    website_handler = webpage_handler.WebPageHandler(model_name,
                                                     model_database.get_balances(),
                                                     model_database.get_predicted_correctly())

    # initialize variables
    state = STATES["START"]

    while True:
        state = await_next_state(driver, state)

        if state == STATES["BETS_OPEN"]:
            print('BETS_OPEN')

            red, blue = driver.get_fighters()

            if (red, blue) is None:  # names are not available yet...
                time.sleep(1)
                state = STATES['START']
                continue

            print(f'{red} vs {blue}')

            confidence = model.predict_match(red, blue)

            if confidence is None:  # both characters unknown, wait for next match
                time.sleep(5)
                state = STATES['START']
                continue

            else:  # At least one fighter known
                predicted_winner = int_to_team(np.around(confidence))

                # Adjust confidence to reflect predicted pred_str as the larger number
                if predicted_winner == 'blue':
                    confidence = 1 - confidence

                confidence = min(max(confidence, 0.5), 1.0)             # confidence is now limited between 0.5 and 1
                confidence = (confidence - 0.5) * 2                     # confidence is now scaled between 0 and 1
                bet_amount = gambler.calculate_bet(confidence, driver)  # calculate bet amount

            driver.bet(max(bet_amount, 1), predicted_winner)
            website_handler.update_page(
                match_confidence=confidence,
                team_prediction=predicted_winner,
                red_name=red,
                blue_name=blue,
                bet_amount=bet_amount,
            )
            continue

        if state == STATES['BETS_CLOSED']:
            print("Bets closed")
            odds = driver.get_odds()

            # wait for odds to be readable if we could not grab them in the first pass
            while odds is None:
                odds = driver.get_odds()
                time.sleep(1)

            website_handler.update_page(
                match_confidence=confidence,
                team_prediction=predicted_winner,
                red_name=red,
                blue_name=blue,
                bet_amount=bet_amount,
                odds=odds,
            )
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
            predicted_correctly = winner == predicted_winner

            model_database.add_entry(predicted_correctly, confidence, end_balance)
            website_handler.update_page(
                match_confidence=confidence,
                team_prediction=predicted_winner,
                red_name=red,
                blue_name=blue,
                bet_amount=bet_amount,
                odds=odds,
                winner=winner,
                end_balance=end_balance,
            )


def start():
    if len(sys.argv) != 4:
        print("Usage: python3 model_driver_main.py <model_name> <gambler_id> <user_id>")
        sys.exit(1)

    print(sys.argv)

    model_name = sys.argv[1]
    gambler_id = sys.argv[2]
    user_id = sys.argv[3]

    from base.base_gambler import GAMBLER_ID_DICT
    gambler = GAMBLER_ID_DICT[int(gambler_id)]

    with open('/opt/saltybet/database/user_id.json') as f:
        users = json.load(f)['users']

    email = None
    password = None
    for user in users:
        if user['name'] == user_id:
            email = user['user_email']
            password = user['user_password']
            break

    if email is None or password is None:
        print("Could not find user with id " + user_id)
        sys.exit(1)

    main(model_name, gambler, email, password)


if __name__ == '__main__':
    start()
