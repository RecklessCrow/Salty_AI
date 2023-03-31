import onnxruntime as ort
from onnxruntime.capi.onnxruntime_pybind11_state import InvalidArgument
from sqlalchemy.orm import Session

import utils.database as db
from app.utils.settings import settings
from utils.driver import SaltyBetDriver
from utils.utils import *


def main():
    print("Loading model... ", end="")
    model = ort.InferenceSession(settings.MODEL_PATH)
    print("Done!")

    print("Loading driver... ", end="")
    driver = SaltyBetDriver()
    print("Done!")
    print(LINE_SEPERATOR)

    state = STATES["START"]
    winnings = 0
    t_winnings = 0
    match_count = 0
    match_correct = 0
    random_choice = False

    while True:
        state = await_next_state(driver, state)
        match state:
            case 1:  # Bets Open
                red, blue = driver.get_fighters()

                if None in (red, blue):  # Names are not available yet...
                    time.sleep(1)
                    state = STATES["START"]
                    continue

                # Predict winner
                with Session(db.engine) as session:
                    red_idx, blue_idx = db.get_idxs(red, blue, session)

                if None not in [red_idx, blue_idx]:
                    model_input = np.array([[red_idx, blue_idx]]).astype(np.int32)

                    try:
                        pred = model.run(None, {"input_1": model_input})[0][0]
                    except InvalidArgument:
                        continue

                    pred = softmax(pred)
                    conf = np.max(pred)
                    team = 'red' if np.argmax(pred) == 0 else 'blue'

                    bet_amount = calc_bet(
                        balance=driver.get_current_balance(),
                        conf=conf,
                    )
                    random_choice = False

                else:
                    bet_amount = 1000
                    team = np.random.choice(["red", "blue"])
                    conf = np.NaN
                    random_choice = True

                driver.place_bet(bet_amount, team)
                print(f"{red} vs. {blue}")
                print(f"Current Balance: {int_to_money_str(driver.get_current_balance())}")
                print(f"Placed {int_to_money_str(bet_amount)} on {team.capitalize()} ({conf:.0%} confident)")

            case 2:  # Bets Closed
                red_odds, blue_odds = driver.get_odds()
                print(f"Odds - {red_odds} : {blue_odds}")

            case 3:  # Payout
                payout_message = driver.get_game_state()

                if "red" in payout_message:
                    winner = "red"

                elif "blue" in payout_message:
                    winner = "blue"

                else:  # Tie, do not record
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
                    print(f"Match Payout:           {int_to_money_str(match_payout)}")
                else:
                    print(f"Tournament Winnings:    {int_to_money_str(t_winnings)}")
                print(f"Session Winnings:       {int_to_money_str(winnings)}")
                print(f"Session Accuracy: {match_correct / match_count:.2%} | {match_count} matches")
                print(LINE_SEPERATOR)

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
    main()
