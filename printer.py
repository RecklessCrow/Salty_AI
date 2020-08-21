old_balance = 0
old_bet_amount = 0
old_gain = 0
old_prediction = ''

num_games_bet = 0
num_games_won = 0
winnings = 0


def print_idle(info):
    betting_amount, potential_gain, red_odds, blue_odds = info

    print(
        f'${red_odds} : {blue_odds} | {betting_amount:,} -> ${potential_gain:,}\n'
        f'Percent of balance bet: {betting_amount / old_balance:.2%}'
    )

    global old_bet_amount, old_gain
    old_bet_amount = betting_amount
    old_gain = betting_amount


def print_match(info):
    red, blue, balance, prediction, probability = info

    print(
        f'Current balance: ${balance:,}\n'
        f'{red} vs. {blue} | {prediction} : {probability:.2%}'
    )

    global old_balance, old_prediction
    old_balance = balance
    old_prediction = prediction


def print_payout(winner):
    global old_prediction, old_gain, old_bet_amount, winnings, num_games_won, num_games_bet

    correct = old_prediction == winner
    payout = old_gain if correct else -old_bet_amount
    winnings += payout

    num_games_won += 1 if correct else 0
    num_games_bet += 1

    print(
        f'Winner: {winner} | {"Correct" if correct else "Incorrect"} prediction\n'
        f'Match payout      = {payout:+,}\n'
        f'Current winnings  = {winnings:+,}\n'
        f'Current accuracy  = {num_games_won / num_games_bet:.2%}\n'
    )
