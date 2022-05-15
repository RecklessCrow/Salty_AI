import numpy as np
from sigfig import round

from Utils import *
from src.Model.Model import Model
from src.SaltyBetDriver import SaltyBetDriver

MODLE_FILE = "SavedModels/model_15.14.00"
BALANCE_CAP = 10_000

ALL_IN = False
ALL_IN_CONFIDENCE_LEVEL = 0.9
MAX_BET_PERCENT = 0.2


def main():
    model = Model(database.get_num_characters(), MODLE_FILE)

    driver = SaltyBetDriver(headless=False)
    state = STATES["IDLE"]
    start = time.time()
    wins = 0
    matches = 0
    team = ""

    while True:
        state = await_next_state(driver, state)

        if state == STATES["BETS_OPEN"]:
            red, blue = driver.get_fighters()
            is_tournament = driver.is_tournament()
            bailout = driver.get_bailout(is_tournament)
            balance = driver.get_balance()

            if "team" in red.lower() or "team" in blue.lower():
                bet_amount = 1
                pred = np.around(np.random.random())  # coin flip
                confidence = 0

            else:
                x = database.encode_character([[red], [blue]]).reshape(1, 2)

                confidence = model.predict(x)[0][0]
                pred = np.around(confidence)

                # Adjust percentage for different teams
                if pred == 0:
                    confidence = 1 - confidence

                # Tournament betting rules
                if is_tournament:
                    bet_amount = np.floor(balance * confidence)

                    if bet_amount < bailout:
                        bet_amount = bailout

                # Bet all in if we're less than 2x buy in
                elif balance < 2 * bailout:
                    bet_amount = balance

                # Bet all in if we're above a certain confidence level
                elif confidence > ALL_IN_CONFIDENCE_LEVEL:
                    bet_amount = balance if ALL_IN else balance * MAX_BET_PERCENT

                else:
                    if balance < BALANCE_CAP:
                        bet_amount = np.floor(balance * confidence) // 4
                    else:
                        bet_amount = np.floor(min(balance * confidence, balance * 0.01))

            if bet_amount > balance:
                bet_amount = balance

            bet_amount = round(int(bet_amount), sigfigs=1)

            team = database.int_to_team(pred)

            try:
                print(
                    f"Red  Team: {red}\n"
                    f"Blue Team: {blue}"
                )

            except ValueError:
                print(
                    f"Fighter names in poor format, unable to print."
                )

            print(
                f"Betting ${bet_amount:,} on {team.capitalize()} Team\n"
                f"Model confidence: {confidence:.2%}"
            )

            driver.bet(max(bet_amount, 1), team)
            continue

        if state == STATES["PAYOUT"]:
            match_time = time.time() - start
            start = time.time()
            matches += 1
            wins = record_match(driver, match_time, team, matches, wins)


if __name__ == '__main__':
    main()
