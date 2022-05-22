import time

from sigfig import round

from DatabaseHandler import DatabaseHandler

"""
Utilities for the state machines
"""

DATABASE = DatabaseHandler()

MODLE_FILE = "SavedModels/model_01.14.24"

UNKNOWN_FIGHTER = 0

# Betting parameters
BALANCE_CAP = 10_000
HIGH_CONFIDENCE = 0.8
ALL_IN_CONFIDENCE = 0.95
MAX_NORMAL_BET = 100_000

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
        bet_amount = balance * confidence

        if bet_amount < bailout:
            bet_amount = bailout

    # Bet all in if we're less than 5x bailout
    elif balance < 5 * bailout:
        bet_amount = balance

    # Bet all in if we're above a certain confidence level
    elif confidence > HIGH_CONFIDENCE:
        if confidence > ALL_IN_CONFIDENCE:
            bet_amount = balance if balance < 1e6 else (balance * confidence) / 2
        else:
            bet_amount = (balance * confidence) / 4

    # normal betting rules
    else:
        if balance < BALANCE_CAP:
            bet_amount = balance * margin
        else:
            bet_amount = balance * 0.05

        bet_amount = min(MAX_NORMAL_BET, bet_amount)

    bet_amount = round(int(bet_amount), sigfigs=3)

    if bet_amount > balance:
        bet_amount = balance

    return bet_amount


def await_next_state(driver, last_state):
    state = last_state

    while state == last_state:
        state = decode_state(driver.get_game_state())
        time.sleep(1)

    return state
