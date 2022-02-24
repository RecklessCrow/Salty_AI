import numpy as np

from Utils import *
from src.Model.Model import Model
from src.SaltyBetDriver import SaltyBetDriver

model_file = "SavedModels/model_15.14.00"


def main():
    model = Model(database.get_num_characters(), model_file)

    driver = SaltyBetDriver(headless=False)
    state = STATES["IDLE"]
    start = time.time()

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

                if pred == 0:
                    confidence = 1 - confidence
                if balance < 2 * bailout or confidence > 0.9:
                    bet_amount = balance

                elif is_tournament:
                    bet_amount = np.floor(balance * confidence)

                    if bet_amount < bailout:
                        bet_amount = bailout

                else:
                    if balance < 10_000:
                        bet_amount = np.floor(balance * confidence) // 2
                    else:
                        bet_amount = np.floor(min(balance * confidence, balance * 0.01))

            if bet_amount > balance:
                bet_amount = balance

            bet_amount = int(bet_amount)

            team = database.int_to_team(pred)
            print(
                f"Red  Team: {red}\n"
                f"Blue Team: {blue}\n"
                f"Betting ${bet_amount:,} on {team.capitalize()} Team\n"
                f"Model confidence: {confidence:%}"
            )
            driver.bet(max(bet_amount, 1), team)
            continue

        if state == STATES["PAYOUT"]:
            match_time = time.time() - start
            start = time.time()
            record_match(driver, match_time)


if __name__ == '__main__':
    main()
