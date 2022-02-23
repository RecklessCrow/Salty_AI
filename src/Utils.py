import time

from DatabaseHandler import DatabaseHandler
from SaltyBetDriver import SaltyBetDriver

"""
Utilities for the state machines
"""

database = DatabaseHandler()
driver = SaltyBetDriver(headless=True)

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


def await_next_state(last_state):
    state = last_state

    while state == last_state:
        state = decode_state(driver.get_game_state())
        time.sleep(1)

    return state
