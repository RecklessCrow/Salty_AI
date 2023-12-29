import logging

from database.interface import db
from utils.betting_module import betting_module
from utils.state_machine import StateMachine
from utils.web_driver import saltybet


def main(logger):
    # Start the state machine
    machine = StateMachine()
    machine.start()

    # Initialize the session variables
    session_winnings = 0
    bets_started = False

    match_info = {}

    while True:
        state = machine.await_next_state()

        match state:
            case machine.States.BETS_OPEN:
                # Get the current match up
                red, blue = saltybet.get_match_up()

                if "team" in red.lower() or "team" in blue.lower():
                    # Skip if the match is an exhibition match
                    logger.info("Exhibition match, skipping...")
                    continue

                # Set the bets started flag
                bets_started = True

                # Calculate the wager amount
                balance = saltybet.get_balance()
                is_tournament = saltybet.is_tournament()
                wager, bet_on = betting_module.get_wager(red, blue, balance, is_tournament)

                result = saltybet.place_bet_with_retry(wager, bet_on)
                if not result:
                    # If the bet was not placed, skip this iteration
                    match_info = None
                    continue

                match_info = {
                    "red": red,
                    "blue": blue,
                    "balance": balance,
                    "wager": wager,
                    "team_bet_on": bet_on,
                    "is_tournament": is_tournament,
                }

                logger.info(
                    f"{red} vs {blue}\n"
                    f"          Bet on: {bet_on}\n"
                    f"          Wager:              {betting_module.int_to_money(wager)}"
                )

            case machine.States.BETS_CLOSED:
                # Case where we start the program while bets are closed
                if not bets_started:
                    continue

                # Case where the driver failed to place the bet
                if not match_info:
                    continue

                red_pot, blue_pot = saltybet.get_pots()

                # Update the match info
                match_info["red_pot"] = red_pot
                match_info["blue_pot"] = blue_pot

                logger.info(
                    f"Red pot:            {betting_module.int_to_money(red_pot)}\n"
                    f"          Blue pot:           {betting_module.int_to_money(blue_pot)}"
                )

            case machine.States.PAYOUT:
                # Case where we start the program while in the payout state
                if not bets_started:
                    continue

                if not match_info:
                    continue

                # Get the winner
                winner = saltybet.get_winner()

                # Get the payout
                payout = saltybet.get_payout()

                # Add the payout to the session winnings
                session_winnings += payout
                match_info["session_winnings"] = session_winnings

                red, blue = match_info["red"], match_info["blue"]
                if "Team" not in red or "Team" not in blue:
                    # Add if the match is not an exhibition match
                    red_pot, blue_pot = match_info["red_pot"], match_info["blue_pot"]
                    is_tournament = match_info["is_tournament"]
                    db.add_match(red, blue, winner, red_pot, blue_pot, is_tournament)

                # Reset the bets started flag
                bets_started = False

                logger.info(
                    f"Winner: {winner}\n"
                    f"          Payout:             {betting_module.int_to_money(payout)}\n"
                    f"          Balance:            {betting_module.int_to_money(saltybet.get_balance())}\n"
                    f"          Session winnings:   {betting_module.int_to_money(session_winnings)}"
                )


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("Main")
        logger.info("Starting SaltyBet Bot")
        main(logger)
    except Exception as e:
        saltybet.__del__()  # Close the browser
        raise e
