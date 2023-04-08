import copy
from functools import partial
from multiprocessing import pool

import numpy as np
import onnxruntime as ort
from sqlalchemy.orm import Session, aliased

import app.utils.database as db
from app.utils.helper_functions import sigmoid, convert_to_money_str
from utils.settings import settings

# Get matches with pots
with Session(db.engine) as session:
    red = aliased(db.Character)
    blue = aliased(db.Character)

    match_data = session.query(
        red.id,
        blue.id,
        db.Match.winner,
        db.MatchMetadata.red_pot,
        db.MatchMetadata.blue_pot
    ).where(
        db.Match.red == red.name
    ).where(
        db.Match.blue == blue.name
    ).filter(
        db.Match.id == db.MatchMetadata.match_id
    ).all()

model = ort.InferenceSession(settings.MODEL_PATH)


def calculate_bet_amount(balance, confidence):
    # Calculate the Kelly criterion percentage
    kelly_pct = (confidence - (1 - confidence)) / confidence
    # Limit the Kelly percentage to a maximum of 50% to avoid excessive risk
    kelly_pct = min(kelly_pct, 0.5)
    # Calculate the optimal bet amount based on the Kelly percentage and current balance
    bet_amount = balance * kelly_pct
    # Use a value betting approach to adjust the bet amount based on the confidence level
    if confidence < 0.6:
        bet_amount *= 0.5
    elif confidence < 0.7:
        bet_amount *= 0.75
    elif confidence < 0.8:
        bet_amount *= 1.25
    else:
        bet_amount *= 1.5
    # Round the bet amount to the nearest whole number
    bet_amount = round(bet_amount)
    # Ensure that the bet amount is not greater than the current balance
    bet_amount = min(bet_amount, balance)
    # Return the bet amount
    return bet_amount


def run_sim(idx):
    data = copy.copy(match_data)
    np.random.shuffle(data)

    # Simulate betting
    balances = []
    initial_balance = 750
    balance = initial_balance
    loss_streak = 0

    for red, blue, winner, red_pot, blue_pot in data:
        # predict winner
        model_input = np.array([[red, blue]]).astype(np.int64)
        conf = sigmoid(model.run(None, {"input": model_input})[0].sum())  # Works because we only predict one thing
        pred = round(conf)
        if pred == 0:
            team = 'red'
            conf = 1 - conf
        else:
            team = 'blue'

        # calc bet
        profit = balance - initial_balance
        bet = calculate_bet_amount(balance, conf)

        # add bet amount to team pot
        if team == "red":
            red_pot += bet
        else:
            blue_pot += bet

        # if correct, calc positive return
        if team == winner:
            ratio = max(red_pot, blue_pot) / min(red_pot, blue_pot)

            if max(red_pot, blue_pot) == red_pot:
                popular_team = 'red'
            else:
                popular_team = 'blue'

            if team == popular_team:
                # popular win
                winnings = bet / ratio
            else:
                # upset win
                winnings = bet * ratio

            balance += np.ceil(winnings)

        # else, subtract bet amount from balance
        else:
            balance -= bet

        # check if balance is less than initial balance
        if balance < initial_balance:
            balance = initial_balance

        balances.append(balance)

    return balances


def main():

    balances = []
    for idx in range(100):
        balances.append(run_sim(idx))
    balances = np.array(balances)

    avg_money = np.mean(balances)
    max_money = np.max(balances)

    print(f"Avg Money:  {convert_to_money_str(avg_money)}")
    print(f"Max Money:  {convert_to_money_str(max_money)}")
    print(f"End Money:  {convert_to_money_str(np.mean(balances[:, -1]))}")
    print("-" * 100)


if __name__ == '__main__':
    main()
