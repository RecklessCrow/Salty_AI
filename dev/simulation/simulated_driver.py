import random

import numpy as np


class SaltyBetSim:
    BAILOUT = 100

    def __init__(self, match_list):
        self.matches = [{
            "red": match[0],
            "blue": match[1],
            "winner": match[2],
            "red_odds": match[3],
            "blue_odds": match[4],
            "red_pot": match[5],
            "blue_pot": match[6],
            "is_tournament": match[7],
            "matchup_count": match[8]}
            for match in match_list
        ]
        self.match_index = 0
        self.random_seed = 42
        random.seed(self.random_seed)
        self.shuffle_match_list()
        self.balance = self.BAILOUT

    def shuffle_match_list(self):
        random.shuffle(self.matches)

    def predict_on_all_matches(self, model):
        matchups = np.array([(match['red'], match['blue']) for match in self.matches])
        return model.predict_batch(matchups)

    def get_all_odds(self):
        return np.array([(match['red_odds'], match['blue_odds']) for match in self.matches])

    def get_all_winners(self):
        return np.array([match['winner'] for match in self.matches])

    def get_match(self):
        if self.match_index >= len(self.matches):
            return None, None

        return self.matches[self.match_index]["red"], self.matches[self.match_index]["blue"]

    def set_balance(self, balance):
        self.balance = balance

    def get_odds(self):
        return self.matches[self.match_index]["red_odds"], self.matches[self.match_index]["blue_odds"]

    def get_pots(self):
        return self.matches[self.match_index]["red_pot"], self.matches[self.match_index]["blue_pot"]

    def get_winner(self):
        winner = self.matches[self.match_index]["winner"]
        self.match_index += 1
        return winner

    def is_tournament(self):
        # return self.matches[self.match_index]["is_tournament"]
        return False

    def get_balance(self):
        return int(self.balance)

    def get_bailout(self, is_tournament):
        if is_tournament:
            return self.BAILOUT + 1000

        return self.BAILOUT

    def win(self, amount):
        self.balance += amount

    def lose(self, amount):
        self.balance -= amount

        if self.balance < self.BAILOUT:
            self.balance = self.BAILOUT

    def reset(self):
        self.balance = self.BAILOUT
        self.match_index = 0
        self.shuffle_match_list()
