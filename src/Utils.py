import time

import numpy as np
from sigfig import round

from DatabaseHandler import DatabaseHandler

"""
Utilities for the state machines
"""

DATABASE = DatabaseHandler()

MODLE_FILE = "SavedModels/model_03.35.55"

UNKNOWN_FIGHTER = 0

# Betting parameters
BALANCE_CAP = 100_000
ALL_IN = False
ALL_IN_CONFIDENCE_LEVEL = 0.9

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


def calc_bet_amount(driver, confidence):
    is_tournament = driver.is_tournament()
    bailout = driver.get_bailout(is_tournament)
    balance = driver.get_balance()

    margin = confidence - 0.5

    # Tournament betting rules
    if is_tournament:
        bet_amount = np.floor(balance * confidence)

        if bet_amount < bailout:
            bet_amount = bailout

    # Bet all in if we're less than 5x buy in
    elif balance < 5 * bailout:
        bet_amount = balance

    # Bet all in if we're above a certain confidence level
    elif confidence > ALL_IN_CONFIDENCE_LEVEL:
        bet_amount = float("inf") if ALL_IN else balance * margin

    # normal betting rules
    else:
        if balance < BALANCE_CAP:
            bet_amount = balance * confidence / 2
        else:
            bet_amount = min(balance * margin, balance * 0.01)

    bet_amount = round(int(bet_amount), sigfigs=2)

    if bet_amount > balance:
        bet_amount = balance

    return bet_amount


def await_next_state(driver, last_state):
    state = last_state

    while state == last_state:
        state = decode_state(driver.get_game_state())
        time.sleep(1)

    return state
