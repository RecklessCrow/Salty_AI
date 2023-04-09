import sys
import time

import numpy as np
import onnxruntime as ort
from onnxruntime.capi.onnxruntime_pybind11_state import InvalidArgument
from sqlalchemy.orm import Session

import utils.database as db
from utils.driver import SaltyBetDriver
from utils.helper_functions import (
    await_next_state,
    sigmoid,
    calc_bet,
    convert_to_money_str
)
from utils.settings import settings, States


def main():
    print("Loading development... ", end="")
    model = ort.InferenceSession(settings.MODEL_PATH)
    print("Done!")

    print("Loading driver... ", end="")
    driver = SaltyBetDriver()
    print("Done!")
    print(settings.LINE_SEPERATOR)

    state = States.START
    winnings = 0
    t_winnings = 0
    match_count = 0
    match_correct = 0
    random_choice = False

    while True:
        state = await_next_state(driver, state)
        match state:
            case States.BETS_OPEN:  # Bets Open
                red, blue = driver.get_fighters()

                if None in (red, blue):  # Names are not available yet...
                    time.sleep(settings.WAIT_TIME)
                    state = settings.STATES["START"]
                    continue

                # Predict winner
                with Session(db.engine) as session:
                    red_idx, blue_idx = db.get_idxs(red, blue, session)

                if None not in [red_idx, blue_idx]:
                    try:
                        model_input = np.array([[red_idx, blue_idx]]).astype(np.int64)
                        # Works because we only predict one thing
                        conf = sigmoid(model.run(None, {"input": model_input})[0].sum())
                    except InvalidArgument:
                        continue

                    pred = round(conf)
                    if pred == 0:
                        team = 'red'
                        conf = 1 - conf
                    else:
                        team = 'blue'

                    bet_amount = calc_bet(
                        balance=driver.get_current_balance(),
                        confidence=conf,
                    )
                    random_choice = False

                else:
                    bet_amount = 1000
                    team = np.random.choice(["red", "blue"])
                    conf = np.NaN
                    random_choice = True

                driver.place_bet(bet_amount, team)
                print(f"Game Mode: {'Tournament' if driver.is_tournament() else 'Normals'}")
                print(f"{red} vs. {blue}")
                print(f"Current Balance: {convert_to_money_str(driver.get_current_balance())}")
                print(f"Placed {convert_to_money_str(bet_amount)} on {team.capitalize()} ({conf:.0%} confident)")

            case States.BETS_CLOSED:
                red_odds, blue_odds = driver.get_odds()
                print(f"Odds - {red_odds} : {blue_odds}")

            case States.PAYOUT:
                if (winner := driver.get_winner()) is None:
                    continue

                if not random_choice:
                    match_count += 1
                    if winner == team:
                        match_correct += 1

                match_payout = driver.get_payout()

                if driver.is_tournament():
                    t_winnings += match_payout
                else:
                    winnings += match_payout
                    winnings += t_winnings
                    t_winnings = 0

                print(f"{winner.capitalize()} team wins!")
                if not driver.is_tournament():
                    print(f"Match Payout:           {convert_to_money_str(match_payout)}")
                else:
                    print(f"Tournament Winnings:    {convert_to_money_str(t_winnings)}")
                print(f"Session Winnings:       {convert_to_money_str(winnings)}")
                print(f"Session Accuracy: {match_correct / match_count:.2%} | {match_count} matches")
                print(settings.LINE_SEPERATOR)

                if "team" == red.lower()[:4] or "team" == blue.lower()[:4]:  # Teams are not counted
                    continue

                with Session(db.engine) as session:
                    db.add_match(
                        match_info=(red, blue, winner),
                        match_metadata=driver.get_pots(),
                        session=session,
                        commit=True
                    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(-1)
