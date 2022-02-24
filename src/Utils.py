import time

from DatabaseHandler import DatabaseHandler

"""
Utilities for the state machines
"""

database = DatabaseHandler()


STATES = {
    "IDLE": 0,
    "BETS_OPEN": 1,
    "PAYOUT": 2
}


def decode_state(encoded_state):
    if "locked" in encoded_state:
        return STATES["IDLE"]

    if "open" in encoded_state:
        return STATES["BETS_OPEN"]

    if "payout" in encoded_state:
        return STATES["PAYOUT"]

    return STATES["IDLE"]


def await_next_state(driver, last_state):
    state = last_state

    while state == last_state:
        state = decode_state(driver.get_game_state())
        time.sleep(1)

    return state


def record_match(driver, match_time):
    payout_message = driver.get_game_state()

    if "red" in payout_message:  # red winner
        winner = "red"
    elif "blue" in payout_message:  # blue winner
        winner = "blue"
    else:  # tie
        return

    print(
        f"{winner.capitalize()} Team Wins!\n"
        f"Match time: {time.strftime('%M:%S', time.gmtime(match_time))}\n"
        f"--------------------"
    )

    red, blue = driver.get_fighters()

    if "team" in red.lower() or "team" in blue.lower():
        return

    database.match_over(red, blue, winner)
