from utils.database_handler import MatchDatabaseHandler
from utils.salty_bet_driver import HomepageDriver
from utils.state_machine_utils import *


def main():
    database = MatchDatabaseHandler("homepage_matches")
    driver = HomepageDriver()
    state = STATES["START"]  # initial state

    while True:  # main feedback loop
        state = await_next_state(driver, state)

        if state == STATES["BETS_OPEN"]:
            # todo Get and display fighters to website
            red, blue = driver.get_fighters()
            continue

        if state == STATES["BETS_CLOSED"]:
            # todo Get and display odds, money pots, ect. to website
            red_odds, blue_odds = driver.get_odds()
            continue

        if state == STATES["PAYOUT"]:
            # todo Get and display winner to website

            # Add match to database
            payout_message = driver.get_game_state()

            if "red" in payout_message:
                winner = "red"

            elif "blue" in payout_message:
                winner = "blue"

            else:
                continue

            # @TODO: add odds to database?
            red, blue = driver.get_fighters()
            if not ("team" == red.lower()[:4] or "team" == blue.lower()[:4]):
                database.add_match(red, blue, winner)


if __name__ == '__main__':
    main()
