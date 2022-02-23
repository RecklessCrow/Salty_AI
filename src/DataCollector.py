from Utils import *

"""
Script to gather match data.
Same state machine as Gambler.py but without any betting logic.
"""


def main():
    state = STATES["IDLE"]
    start = time.time()

    while True:
        state = await_next_state(state)

        if state == STATES["PAYOUT"]:
            match_time = time.time() - start
            start = time.time()

            payout_message = driver.get_game_state()

            if "red" in payout_message:  # red winner
                winner = "red"
            elif "blue" in payout_message:  # blue winner
                winner = "blue"
            else:  # tie
                continue

            red, blue = driver.get_fighters()

            if "team" in red.lower() or "team" in blue.lower():
                continue

            database.match_over(red, blue, winner)

            print(
                f"{red} vs. {blue}\n"
                f"Match time: {time.strftime('%M:%S', time.gmtime(match_time))}\n"
                f"Current matches in database: {database.get_num_matches():,}\n"
                f"--------------------"
            )

            start = time.time()


if __name__ == '__main__':
    main()
