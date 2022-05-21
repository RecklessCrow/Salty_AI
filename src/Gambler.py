import numpy as np

from Utils import *
from src.Model.Model import Model
from src.SaltyBetDriver import SaltyBetDriver


def main(headless):
    model = Model(filepath=MODLE_FILE)
    driver = SaltyBetDriver(headless=headless)

    state = STATES["IDLE"]

    pred = None
    wins = 0
    matches = 0

    while True:
        state = await_next_state(driver, state)

        if state == STATES["BETS_OPEN"]:
            red, blue = driver.get_fighters()

            if (red, blue) is None:
                continue

            fighter_vector = DATABASE.encode_character([[red], [blue]]).reshape(1, 2)

            if UNKNOWN_FIGHTER not in fighter_vector:
                confidence = model.predict(fighter_vector)[0][0]
                pred = np.around(confidence)

                # Adjust confidence to reflect predicted pred_str as the larger number
                if pred == 0:
                    confidence = 1 - confidence

                bet_amount = calc_bet_amount(driver, confidence)

            # Unknown fighter present
            else:
                bet_amount = 1
                pred = np.random.choice([0, 1])  # coin flip
                confidence = 0

            pred_str = DATABASE.int_to_team(pred)

            print(
                f"Red  Team: {red}\n"
                f"Blue Team: {blue}\n"
                f"Betting ${bet_amount:,} on {pred_str.capitalize()} Team\n"
                f"Model confidence: {confidence:.2%}\n"
                f"Tournament: {driver.is_tournament()}"
            )

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

            print(
                f"{winner.capitalize()} Team Wins!\n"
                f"Current Model Accuracy: {wins / matches:.2%} | {matches} matches\n"
                f"Ending Balance: ${driver.get_balance()}\n"
                f"{'-' * 30}"
            )

            red, blue = driver.get_fighters()
            if not ("team" in red.lower() or "team" in blue.lower()):
                DATABASE.match_over(red, blue, winner)


if __name__ == '__main__':
    headless = None
    while headless is None:
        response = input("Run in headless mode? y/n: ")
        if response not in ['y', 'n']:
            continue

        headless = response == "y"

    main(headless)
