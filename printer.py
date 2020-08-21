old_balance = 0
winnings = 0
old_prediction = ''


def print_idle(info):
    betting_amount, potential_gain, red_odds, blue_odds, balance = info
    print(
        f'${betting_amount:,} -> ${potential_gain:,} | {red_odds} : {blue_odds}\n'
        f'Percent of balance bet: {betting_amount / balance:.2%}'
    )


def print_match(info):
    red, blue, balance, prediction, probability = info
    print(
        f'Current balance: ${balance:,}\n'
        f'{red} vs. {blue} | {prediction} : {probability:.2%}'
    )
    global old_balance, old_prediction
    old_balance = balance
    old_prediction = prediction


def print_payout(info):
    winner, new_balance = info
    global old_balance, winnings, old_prediction
    payout = new_balance - old_balance
    winnings += payout
    print(
        f'Winner: {winner}\n'
        f'{"Correct" if old_prediction == winner else "Incorrect"} prediction\n'
        f'Payout = {payout:+,}\n'
        f'Current winnings = {winnings:+,}\n'
    )
