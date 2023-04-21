import threading
import time

from utils.driver import driver
from utils.helper_functions import (
    predict_winner,
    calculate_bet,
    int_to_money,
    money_to_int,
    update_json
)
from utils.settings import settings
from utils.state_machine import StateMachine

# Import the database if we have a DSN
if settings.PG_DSN is not None:
    import utils.database as db


def main():
    # Start the state machine
    machine = StateMachine()
    states = machine.States
    update_thread = threading.Thread(target=machine.update_state, daemon=True)
    update_thread.start()

    # Initialize the session variables
    session_winnings = 0
    web_json = {}
    start_time = None
    num_matches = 0
    num_correct = 0

    while True:
        web_json["balance"] = int_to_money(driver.get_balance())
        update_json(web_json)
        state = machine.await_next_state()

        match state:
            case states.BETS_OPEN:
                # Get the current match up
                red, blue = driver.get_match_up()

                # Predict the winner
                conf, team = predict_winner(red, blue)

                # Calculate the bet amount
                balance = driver.get_balance()
                is_tournament = driver.is_tournament()
                bet = calculate_bet(balance, conf, is_tournament)

                # Place a bet
                driver.place_bet(bet, team)

                # Update the web json with the new data
                web_json["red"] = red
                web_json["blue"] = blue
                web_json["bet"] = int_to_money(bet)
                web_json["team_bet_on"] = team
                web_json["confidence"] = f"{conf:.2%}"
                web_json["is_tournament"] = is_tournament

            case states.BETS_CLOSED:
                # Start timer for match duration
                start_time = time.time()

                try:
                    red_pot, blue_pot = driver.get_pots()
                    red_odds, blue_odds = driver.get_odds()
                except RuntimeError:
                    red_pot, blue_pot = 0, 0
                    red_odds, blue_odds = 0, 0

                # Get the popular team
                popular_team = "red" if red_pot > blue_pot else "blue"
                # Get the odds of the popular team
                popular_odds = red_odds if popular_team == "red" else blue_odds

                # Calculate the payout
                bet = money_to_int(web_json["bet"])
                if web_json["team_bet_on"] == popular_team:
                    payout = bet / popular_odds
                else:
                    payout = bet * popular_odds

                # Update the web json with the new data
                web_json["red_pot"] = int_to_money(red_pot)
                web_json["blue_pot"] = int_to_money(blue_pot)
                web_json["red_odds"] = red_odds
                web_json["blue_odds"] = blue_odds
                web_json["potential_payout"] = int_to_money(payout)

            case states.PAYOUT:
                # Calculate the match duration
                match_duration = time.time() - start_time

                # Get the winner
                winner = driver.get_winner()

                # Get the payout
                payout = driver.get_payout()

                # Add the payout to the session winnings
                session_winnings += payout

                # Calculate running average for model accuracy
                num_matches += 1
                if web_json["team_bet_on"] == winner:
                    num_correct += 1
                accuracy = num_correct / num_matches

                # Reset the web json and update it with the new data
                red, blue = web_json["red"], web_json["blue"]
                pots = money_to_int(web_json["red_pot"]), money_to_int(web_json["blue_pot"])
                web_json = {
                    "last_red": red,
                    "last_blue": blue,
                    "winner": winner,
                    "payout": int_to_money(payout),
                    "session_winnings": int_to_money(session_winnings),
                    "match_duration": f"{match_duration:.2f}",
                    "accuracy": f"{accuracy:.2%}",
                }

                if settings.PG_DSN is not None:
                    # Add the match to the database
                    db.add_match(red, blue, winner, pots)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        driver.__del__()  # Close the browser
        raise e
