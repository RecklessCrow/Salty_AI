from sklearn.preprocessing import OneHotEncoder

from logger_script import logger
from collections import deque
import database_handler
import numpy as np
import random

te = OneHotEncoder()
te.fit(np.array(['P', 'B', 'A', 'S', 'X']).reshape(-1, 1))
label_encoder = OneHotEncoder()
label_encoder.fit([['red'], ['blue']])


class Memory:

    def __init__(self, maxlen=5000):
        self.mem_x, self.mem_y = deque(maxlen=maxlen), deque(maxlen=maxlen)

        memory_buffer_size = 1000
        self._populate_memory(memory_buffer_size)

    def _populate_memory(self, num):
        x, y = database_handler.select_num_matches(num)
        # x = np.dstack((x, np.zeros((len(x), 2, 5))))
        self.mem_x.extend(x)
        self.mem_y.extend(y)

    def get_memories(self, num_memories=50):
        if len(self) < num_memories:
            num_memories = len(self)

        idxs = random.sample(range(len(self)), num_memories)

        x = np.array(self.mem_x).take(idxs, axis=0)
        y = np.array(self.mem_y).take(idxs, axis=0)

        return x, y

    def add_memory(self, x, y):
        self.mem_x.append(x)
        self.mem_y.append(y)

    def __len__(self):
        return len(self.mem_x)


old_balance = 0
old_bet_amount = 0
old_gain = 0
old_prediction = ''

num_games_bet = 0
num_games_won = 0
winnings = 0

idle_msg = ''
match_msg = ''


def print_idle(info):
    betting_amount, potential_gain, red_odds, blue_odds = info

    msg_str = f'Percent of balance bet: {betting_amount / old_balance:.2%}\n' \
              f'{red_odds} : {blue_odds} | ${betting_amount:,} -> ${potential_gain:,}'

    print(msg_str)

    global old_bet_amount, old_gain, idle_msg
    old_bet_amount = betting_amount
    old_gain = potential_gain
    idle_msg = msg_str


def print_match(info):
    red, blue, balance, prediction, probability = info

    msg_str = f'Match #{num_games_bet + 1:,}\n' \
              f'{red} vs. {blue} | {prediction} : {probability:.2%}\n' \
              f'Current balance: ${balance:,}'

    print(msg_str)

    global old_balance, old_prediction, match_msg
    old_balance = balance
    old_prediction = prediction
    match_msg = msg_str


def print_payout(winner):
    global winnings, num_games_won, num_games_bet

    correct = old_prediction == winner
    payout = old_gain if correct else -old_bet_amount

    # while under 10_000 we always bet all in, so add the base amount from the display
    if payout < 0 and old_balance < 10_000:
        payout += 3650
    winnings += payout

    num_games_won += 1 if correct else 0
    num_games_bet += 1

    msg_str = f'Winner: {winner} | {"Correct" if correct else "Incorrect"} prediction\n' \
              f'Match payout      = {payout:+,}\n' \
              f'Current winnings  = {winnings:+,}\n' \
              f'Current accuracy  = {num_games_won / num_games_bet:.2%}\n'

    print(msg_str)

    logger.info('\n' + match_msg + '\n' + idle_msg + '\n' + msg_str)


if __name__ == "__main__":
    mem = Memory()
    x, y = mem.get_memories()
    print(x)
