from utils.database_handler import HomepageDatabaseHandler
from utils.salty_bet_driver import HomepageDriver
from utils.state_machine_utils import *


def main():
    database = HomepageDatabaseHandler()
    driver = HomepageDriver()
    state = STATES["START"]  # initial state

    while True:  # main feedback loop
        state = await_next_state(driver, state)

        if state == STATES["BETS_OPEN"]:
            # todo Get and display fighters to website
            red, blue = driver.get_fighters()
            is_tournament = driver.is_tournament()
            tier = driver.get_tier()
            matchup_count = database.get_matchup_count(red, blue)
            continue

        if state == STATES["BETS_CLOSED"]:
            # todo Get and display odds, money pots, ect. to website
            red_odds, blue_odds = driver.get_odds()
            red_pot, blue_pot = driver.get_pot()
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

            if not ("team" == red.lower()[:4] or "team" == blue.lower()[:4]):
                database.add_match(
                    red=red, blue=blue, winner=winner,
                    red_odds=red_odds, blue_odds=blue_odds,
                    red_pot=red_pot, blue_pot=blue_pot,
                    tier=tier,
                    is_tournament=is_tournament,
                    matchup_count=matchup_count
                )


if __name__ == '__main__':
    main()
