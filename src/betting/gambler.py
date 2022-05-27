import numpy as np
from termcolor import colored

from salty_bet_driver import SaltyBetDriver
from src.model.model import Model
from utils import *


def main(headless):
    model = Model(filepath=MODEL_FILE)
    driver = SaltyBetDriver(headless=headless)

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

            red_int, blue_int = DATABASE.encode_character([red, blue])

            # At least one fighter known
            if not (red_int == 0 and blue_int == 0):
                fighter_vector = np.array([[red_int, blue_int]])
                confidence = model.predict(fighter_vector)[0][0]
                pred = np.around(confidence)

                # Adjust confidence to reflect predicted pred_str as the larger number
                if pred == 0:
                    confidence = 1 - confidence

                confidence = (confidence - 0.5) * 2
                matchup_count = DATABASE.get_matchup_count(red, blue)
                matchup_rate = lambda count_seen: 1 - ((2 - count_seen) * 0.1)
                scaled_confidence = confidence * matchup_rate(matchup_count)

                bet_amount = calc_bet_amount3(driver, scaled_confidence)

            # Both fighters unknown, bet on random team
            else:
                bet_amount = 1
                pred = np.random.choice([0, 1])  # coin flip
                confidence = 0
                scaled_confidence = 0
                matchup_count = 0

            pred_str = DATABASE.int_to_team(pred)

            print(
                f"Red  Team: {colored(red, 'red')}\n"
                f"Blue Team: {colored(blue, 'blue')}\n"
                f"Betting {colored(f'${bet_amount:,}', 'green')} on {colored(pred_str.upper(), pred_str)} Team \n"
                f"Model confidence:  {confidence:<7.2%}\n"
                f"Scaled confidence: {scaled_confidence:<7.2%}\n"
                f"Matchup count: {matchup_count:}"
            )

            betting_balance = driver.get_balance()
            driver.bet(max(bet_amount, 1), pred_str)
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
                if pred_str == winner:
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
                DATABASE.match_over(red, blue, winner)


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
