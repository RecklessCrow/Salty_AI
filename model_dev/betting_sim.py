import copy

import numpy as np
import onnxruntime as ort
from sqlalchemy.orm import Session, aliased

import app.utils.database as db
from app.utils.helper_functions import sigmoid, convert_to_money_str
from app.utils.settings import settings

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
    # Set the maximum bet as a fraction of our balance (e.g., 10%)
    max_bet_fraction = 0.5
    max_bet = max_bet_fraction * balance

    # Calculate the optimal bet size based on the confidence level
    bet = max_bet * (2 * confidence - 1)

    # Round the bet to the nearest integer (you can modify this as needed)
    bet = round(bet)

    # Make sure the bet is within our balance limits
    bet = min(bet, max_bet)  # don't bet more than we have or can afford
    bet = max(bet, 750 - balance)  # don't bet less than what we need to reach the minimum balance

    return bet


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
