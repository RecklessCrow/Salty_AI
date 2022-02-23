import numpy as np

from Utils import *
from src.Model.Model import Model


def main():
    state = STATES["IDLE"]
    model = Model(database.get_num_characters())

    while True:
        state = await_next_state(state)

        if state == STATES["BETS_OPEN"]:
            red, blue = driver.get_fighters()
            x = [database.encode_character(red), database.encode_character(blue)]

            pred = np.around(model.predict(x)).flatten()[0]

            # Bet 50%
            bet_amount = driver.get_balance() // 2
            driver.bet(bet_amount, "red" if pred else "blue")

        if state == STATES["PAYOUT"]:
            payout_message = driver.get_game_state()

            # Print some info
            red, blue = driver.get_fighters()

            if "red" in payout_message:  # red winner
                winner = "red"
            elif "blue" in payout_message:  # blue winner
                winner = "blue"
            else:  # tie
                continue

            database.match_over(red, blue, winner)

            continue


if __name__ == '__main__':
    main()
