import time

STATES = {
    "START": 0,
    "BETS_OPEN": 1,
    "BETS_CLOSED": 2,
    "PAYOUT": 3,
}

TEAM_LIST = ['red', 'blue']


def team_to_int(team):
    assert team in TEAM_LIST, "Invalid team"
    return TEAM_LIST.index(team)


def int_to_team(number):
    assert number in [0, 1], "Invalid team number"
    return TEAM_LIST[number]


def decode_state(encoded_state):
    if "locked" in encoded_state:
        return STATES["BETS_CLOSED"]

    if "open" in encoded_state:
        return STATES["BETS_OPEN"]

    if "payout" in encoded_state:
        return STATES["PAYOUT"]

    return None


def await_next_state(driver, last_state):
    state = last_state

    # Base case where we wait for a new match to start
    if last_state == STATES["START"]:
        while True:
            if decode_state(driver.get_game_state()) == STATES["BETS_OPEN"]:
                return STATES["BETS_OPEN"]
            time.sleep(1)
            # exit("Waiting for next match to start")

    while state == last_state:
        state = decode_state(driver.get_game_state())
        time.sleep(1)
        exit("Waiting for next state!!!!!!!!!!!!!!!!!!")

        if state is None:
            state = last_state

    return state
