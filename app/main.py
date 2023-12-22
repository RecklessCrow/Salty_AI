import logging
import time

from selenium.common import TimeoutException

from utils.config import config
from utils.db_driver import db
from utils.betting_module import betting_module
from utils.state_machine import StateMachine
from utils.web_driver import driver





def main():
    # Start the state machine
    machine = StateMachine()
    machine.start()

    # Initialize the session variables
    session_winnings = 0
    num_matches = 0
    num_correct = 0
    bets_started = False

    match_info = {}

    while True:
        state = machine.await_next_state()

        match state:
            case machine.States.BETS_OPEN:
                bets_started = True
                # Get the current match up
                red, blue = driver.get_match_up()

                # Predict the winner
                conf, team = betting_module.predict_winner(red, blue)
                red_conf = conf if team == "red" else 1 - conf
                blue_conf = 1 - red_conf

                # Calculate the wager amount
                balance = driver.get_balance()
                is_tournament = driver.is_tournament()
                wager, bet_upset = betting_module.get_wager(conf, balance, is_tournament)

                if bet_upset:
                    # Invert the team
                    bet_on = "red" if team == "blue" else "blue"
                else:
                    bet_on = team

                result = driver.place_bet_with_retry(wager, bet_on)
                if not result:
                    # If the bet was not placed, skip this iteration
                    match_info = None
                    continue

                match_info = {
                    "red": red,
                    "blue": blue,
                    "wager": wager,
                    "team_bet_on": bet_on,
                    "model": config.MODEL_PATH.split("/")[-1],
                    "model_prediction": team,
                    "red_confidence": red_conf,
                    "blue_confidence": blue_conf,
                    "is_tournament": is_tournament,
                }

            case machine.States.BETS_CLOSED:
                # Case where we start the program while bets are closed
                if not bets_started:
                    continue

                # Case where the driver failed to place the bet
                if not match_info:
                    continue

                red_pot, blue_pot = driver.get_pots()
                red_odds, blue_odds = driver.get_odds()

                # Get the popular team
                popular_team = "red" if red_pot > blue_pot else "blue"
                # Get the odds of the popular team
                popular_odds = red_odds if popular_team == "red" else blue_odds

                # Calculate the payout
                wager = betting_module.money_to_int(match_info["wager"])
                if match_info["team_bet_on"] == popular_team:
                    payout = wager / popular_odds
                else:
                    payout = wager * popular_odds

                # Update the match info
                match_info["red_pot"] = red_pot
                match_info["blue_pot"] = blue_pot
                match_info["payout"] = payout

            case machine.States.PAYOUT:
                # Case where we start the program while in the payout state
                if not bets_started:
                    continue

                # Get the winner
                winner = driver.get_winner()

                # Get the payout
                payout = driver.get_payout()

                # Add the payout to the session winnings
                session_winnings += payout

                # Calculate running average for model accuracy
                num_matches += 1
                if match_info["model_prediction"] == winner:
                    num_correct += 1
                accuracy = num_correct / num_matches

                red, blue = match_info["red"], match_info["blue"]
                if "Team" not in red or "Team" not in blue:
                    # Add if the match is not an exhibition match
                    red_pot, blue_pot = match_info["red_pot"], match_info["blue_pot"]
                    db.add_match(red, blue, winner, red_pot, blue_pot)
                    db.add

                # Reset the bets started flag
                bets_started = False


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        driver.__del__()  # Close the browser
        raise e
