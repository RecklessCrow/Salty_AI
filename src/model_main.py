import json
import sys

import numpy as np

import website.website_utils
from utils.database_handler import ModelDatabaseHandler
from utils.gamblers import Gambler
from utils.model import Model
from utils.salty_bet_driver import ModelDriver
from utils.state_machine_utils import *
from website import webpage_handler


def main(model_name: str, gambler: Gambler, user, enyc_pass):
    print("Initializing model")
    model = Model(model_name)

    print("Initializing driver")
    driver = ModelDriver(user, enyc_pass)

    print("Initializing database")
    model_database = ModelDatabaseHandler(model_name)

    print("Initializing website")
    website_handler = webpage_handler.WebPageHandler(
        model_name,
        model_database.get_balances(),
        model_database.get_predicted_correctly()
    )

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

            prediction = model.predict_match(red, blue)

            if prediction is None:  # both characters unknown, wait for next match
                time.sleep(5)
                state = STATES['START']
                continue

            else:  # At least one fighter known
                predicted_winner = int_to_team(np.argmax(prediction))
                confidence = np.max(prediction)
                confidence = (confidence - 0.5) * 2  # confidence is now scaled between 0 and 1
                bet_amount = gambler.get_bet_amount(confidence, driver)  # calculate bet amount

            driver.place_bet(bet_amount, predicted_winner)
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

            if not driver.is_tournament():
                model_database.add_match(
                    predicted_correctly=winner == predicted_winner,
                    confidence=confidence,
                    end_balance=end_balance,
                )

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
        print("Usage: python3 model_main.py <model_name> <gambler_id> <user_id>")
        sys.exit(1)

    print(sys.argv)

    model_name = sys.argv[1]
    gambler_id = sys.argv[2]
    user_id = sys.argv[3]

    from utils.gamblers import GAMBLER_ID_DICT
    gambler = GAMBLER_ID_DICT[int(gambler_id)]()

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

    website.website_utils.create_run_config(model_name, gambler, user_id)
    main(model_name, gambler, email, password)


if __name__ == '__main__':
    start()
