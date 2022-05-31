import numpy as np
from termcolor import colored
from utils import *

from dev.betting.salty_bet_driver import SaltyBetDriver
from dev.dev_database_handler import DatabaseHandler
from src.utils.gamblers import ExpScaledConfidence
from src.utils.model import Model
from src.utils.state_machine_utils import int_to_team


def main(headless: bool):
    model = Model("")
    driver = SaltyBetDriver(headless=headless)
    gambler = ExpScaledConfidence()
    database = DatabaseHandler()

    state = STATES["IDLE"]

    pred = None
    wins = 0
    matches = 0
    winnings_list = []

    while True:
        state = await_next_state(driver, state)

        if state == STATES["BETS_OPEN"]:

            red, blue = driver.get_fighters()

            if (red, blue) is None:
                continue

            prediction = model.predict_match(red, blue)

            if prediction is None:  # both characters unknown, wait for next match
                time.sleep(5)
                state = STATES['START']
                continue

            else:  # At least one fighter known
                predicted_winner = int_to_team(np.argmax(prediction))
                confidence = np.max(prediction)
                confidence = (confidence - 0.5) * 2  # confidence is now scaled between 0 and 1
                bet_amount = gambler.calculate_bet(confidence, driver)  # calculate bet amount

            print(
                f"Red  Team: {colored(red, 'red')}\n"
                f"Blue Team: {colored(blue, 'blue')}\n"
                f"Betting {colored(f'${bet_amount:,}', 'green')} on {colored(predicted_winner.upper(), predicted_winner)} Team \n"
                f"Model confidence:  {confidence:<7.2%}\n"
            )

            betting_balance = driver.get_balance()
            driver.place_bet(max(bet_amount, 1), predicted_winner)
            continue

        # Match over
        if state == STATES["PAYOUT"]:
            if pred is None:
                continue

            payout_message = driver.get_game_state()

            if "red" in payout_message:  # red winner
                winner = "red"
            elif "blue" in payout_message:  # blue winner
                winner = "blue"
            else:  # tie
                return

            if confidence > 0:
                matches += 1
                if predicted_winner == winner:
                    wins += 1

            # prevent division by zero
            if matches > 0:
                acc = wins / matches
            else:
                acc = 0

            current_balance = driver.get_balance()
            winnings = current_balance - betting_balance
            winnings_list.append(winnings)
            print(
                f"{colored(winner.upper(), winner)} Team Wins!\n"
                f"Model Accuracy: {acc:.2%} | {matches} matches\n"
                f"Model Winnings: {colored(f'${sum(winnings_list):,}', 'green' if sum(winnings_list) > 0 else 'red')}\n"
                f"Match Winnings: {colored(f'${winnings:,}', 'green' if winnings > 0 else 'red')}\n"
                f"Ending Balance: ${current_balance:,}\n"
                f"{'-' * 30}"
            )

            red, blue = driver.get_fighters()
            if not ("team" == red.lower()[:4] or "team" == blue.lower()[:4]):
                database.add_match(red, blue, winner)


if __name__ == '__main__':
    import os

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    headless = None
    while headless is None:
        response = input("Run in headless mode? y/n: ")
        if response not in ['y', 'n']:
            continue

        headless = response == "y"

    main(headless)
