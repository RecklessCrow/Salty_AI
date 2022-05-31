import time
from homepage_utils import database_handler, salty_bet_driver

STATES = {
    "IDLE": 0,
    "BETS_OPEN": 1,
    "PAYOUT": 2
}

DATABASE = database_handler.DatabaseHandler()


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


def main():
    DRIVER = salty_bet_driver.SaltyBetDriver()
    state = STATES["IDLE"]  # initial state

    while True:  # main feedback loop
        state = await_next_state(DRIVER, state)

        if state == STATES["IDLE"]:
            # todo Get and display odds, money pots, ect. to website
            red_odds, blue_odds = DRIVER.get_odds()
            continue

        if state == STATES["BETS_OPEN"]:
            # todo Get and display fighters to website
            red, blue = DRIVER.get_fighters()
            continue

        if state == STATES["PAYOUT"]:
            # Get and display winner to website

            # Add match to database
            payout_message = DRIVER.get_game_state()

            if "red" in payout_message:
                winner = "red"

            elif "blue" in payout_message:
                winner = "blue"

            else:
                continue

            # @TODO: add odds to database
            red, blue = DRIVER.get_fighters()
            if not ("team" == red.lower()[:4] or "team" == blue.lower()[:4]):
                DATABASE.match_over(red, blue, winner)


if __name__ == '__main__':
    main()
