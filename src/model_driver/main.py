import salty_bet_driver
import database_handler
from src.base_gambler import Gambler
from src.model.model import Model
from utils import *
import sys


def main(model_name: str, gambler: Gambler, user, enyc_pass):
    model = Model(filepath=f'../../saved_models/{model_name}')
    driver = salty_bet_driver.SaltyBetDriver()
    database = database_handler.DatabaseHandler(model_name)

    # initialize variables
    state = STATES["START"]
    betting_balance = None

    while True:
        state = await_next_state(driver, state)

        if state == STATES["BETS_OPEN"]:

            red, blue = driver.get_fighters()

            if (red, blue) is None:
                continue

            red_int, blue_int = encode_character([red, blue])

            # At least one fighter known
            if not (red_int == 0 and blue_int == 0):
                fighter_vector = np.array([[red_int, blue_int]])
                confidence = model.predict(fighter_vector)[0][0]
                predicted_winner = np.around(confidence)

                # Adjust confidence to reflect predicted pred_str as the larger number
                if predicted_winner == 0:
                    confidence = 1 - confidence

                bet_amount = gambler.calculate_bet(confidence, driver)

            # Both fighters unknown, bet on random team
            else:
                continue

            pred_str = int_to_team(predicted_winner)
            betting_balance = driver.get_balance()
            driver.bet(max(bet_amount, 1), pred_str)

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

            database.add_entry(predicted_correctly, confidence, end_balance)
            # todo create feed panel with results


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 main.py <model_path>")
        sys.exit(1)

    assert sys.argv[1].isnumeric()
    from src.base_database_handler import DATABASE
    from src.base_gambler import GAMBLER_ID_DICT
    model_name, gambler_id, user, password = DATABASE.get_model_config_by_id(int(sys.argv[1]))
    gambler = GAMBLER_ID_DICT[gambler_id]
    # todo decrypt password
    main('good_model', gambler, user, password)



