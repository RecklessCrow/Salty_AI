import copy
from functools import partial
from multiprocessing import pool

import numpy as np
import onnxruntime as ort
from sqlalchemy.orm import Session, aliased

import app.utils.database as db
from app.utils.helper_functions import softmax
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

rng = np.random.default_rng(1)


def calculate_bet(confidence, balance):
    """
    n = 50,000

    """
    bailout = 750
    all_in_confidence = 0.9
    high_confidence = 0.75
    factor = 1 / 3

    # Bet all in if we're less than 2x bailout
    # Bet all in if we're above a certain confidence level
    if balance < 2 * bailout or confidence >= all_in_confidence:
        bet_amount = balance * (2 * factor)

    # Bet larger amount on matches with higher confidence
    elif confidence > high_confidence:
        bet_amount = balance * factor

    # Normal betting rules
    else:
        bet_amount = balance * confidence * factor

    return bet_amount


def calculate_bet_1(confidence, balance):
    """
    n = 50,000
    Avg Money:      $751,933
    Avg Log Money:  $13
    """
    confidence_slope = -0.13
    start_incline = 0.25
    ceiling_slope = -0.05
    ceiling = 1.0
    aggressive_factor = 10

    log_balance = min(np.log(balance), 13)
    confidence_bias = (log_balance - 5) * confidence_slope + (1.0 - start_incline)
    ceiling_factor = (log_balance - 5) * ceiling_slope + (ceiling / 2)
    ceiling_factor = max(0, ceiling_factor)

    confidence += confidence_bias
    bet_factor = confidence ** aggressive_factor
    x_crossover = ceiling_factor ** (1 / aggressive_factor)
    y_crossover = x_crossover ** aggressive_factor
    if confidence > x_crossover:
        bet_factor = -((x_crossover - (confidence - x_crossover)) ** aggressive_factor) + (y_crossover * 2)

    bet_factor = max(min(bet_factor, 1), 0)
    bet_amount = balance * bet_factor
    return bet_amount


def run_sim(idx, betting_calculator):
    data = copy.copy(match_data)
    rng.shuffle(data)

    # Simulate betting
    initial_balance = 750
    balance = initial_balance
    num_correct = 0
    num_matches = 1
    for red, blue, winner, red_pot, blue_pot in data:
        # predict winner
        model_input = np.array([[red, blue]])
        pred = model.run(None, {"input_1": model_input})[0][0]
        print(pred)
        pred = softmax(pred)
        conf = np.max(pred)
        team = 'red' if np.argmax(pred) == 0 else 'blue'

        # calc bet
        bet = betting_calculator(conf, balance)

        # add bet amount to team pot
        if team == "red":
            red_pot += bet
        else:
            blue_pot += bet

        # if correct, calc positive return
        num_matches += 1
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

            balance += int(np.ceil(winnings))

            num_correct += 1

        # else, subtract bet amount from balance
        else:
            balance -= bet

        # check if balance is less than initial balance
        if balance < initial_balance:
            balance = initial_balance

    return balance


def main():
    # n_runs = 50_000
    # for betting_calculator in [calculate_bet, calculate_bet_1]:
    #     with pool.Pool(32) as p:
    #         balances = p.map(partial(run_sim, betting_calculator=betting_calculator), range(n_runs))
    #
    #     avg_money = np.mean(balances)
    #     log_money = np.mean(np.log(balances))
    #     print(f"Avg Money:      ${int(np.ceil(avg_money)):,}")
    #     print(f"Avg Log Money:  ${int(np.ceil(log_money)):,}")
    #     print(f"Max Money       ${int(max(balances)):,}")
    run_sim(0, calculate_bet)


if __name__ == '__main__':
    main()
