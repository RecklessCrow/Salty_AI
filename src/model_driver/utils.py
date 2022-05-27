import time
import numpy as np
from sklearn.preprocessing import OrdinalEncoder
from src.base_database_handler import DATABASE

STATES = {
    "START": 0,
    "BETS_OPEN": 1,
    "BETS_CLOSED": 2,
    "PAYOUT": 3
}

ENCODER = OrdinalEncoder()
ENCODER.fit(DATABASE.get_all_characters())


def team_to_int(team):
    return int(team == "red")


def int_to_team(number):
    return "red" if number else "blue"


def decode_state(encoded_state):
    if "locked" in encoded_state:
        return STATES["BETS_CLOSED"]

    if "open" in encoded_state:
        return STATES["BETS_OPEN"]

    if "payout" in encoded_state:
        return STATES["PAYOUT"]

    return STATES["START"]


def await_next_state(driver, last_state):
    state = last_state

    # Base case where we wait for a new match to start
    if last_state == STATES["START"]:
        while True:
            if decode_state(driver.get_game_state()) == STATES["BETS_OPEN"]:
                return STATES["BETS_OPEN"]
            time.sleep(1)

    while state == last_state:
        state = decode_state(driver.get_game_state())
        time.sleep(1)

    return state


def encode_character(x, ENCODER):
    """
    Transform character names to integer representations
    :param x: Characters to transform
    :return:
    """

    try:
        encoded_vec = ENCODER.transform(x) + 1

    except ValueError:
        try:
            a = ENCODER.transform([[x[0]]])[0][0] + 1
        except ValueError:
            a = 0

        try:
            b = ENCODER.transform([[x[1]]])[0][0] + 1
        except ValueError:
            b = 0

        encoded_vec = np.array([a, b])

    return encoded_vec


def decode_character(x, ENCODER):
    """
    Transform integer representations to character names
    :param x: integers to transform
    :return:
    """
    unknown = "Unknown Character"

    if isinstance(x, list):
        x = np.array(x).reshape(-1, 1)

    x -= 1

    # Single character
    if isinstance(x, int):
        return ENCODER.inverse_transform([[x]])[0][0] if x != -1 else unknown

    idxs = np.where(x == -1)
    decoded = ENCODER.inverse_transform(x)
    decoded[idxs] = unknown

    return decoded
