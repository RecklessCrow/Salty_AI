import logging
import os
import random
import re

import numpy as np
import onnxruntime as ort

from utils.config import config
from utils.db_driver import db


class BettingModule:

    def __init__(self):
        self.logger = logging.getLogger("BettingModule")
        self.logger.info("Initializing betting module")

        self.min_balance = 10_000
        self.min_balance_tournament = 2 * self.min_balance

        # Load the model
        self.model = ort.InferenceSession(os.path.join(config.MODEL_DIR, 'model.onnx'))

    def predict_winner(self, red, blue):
        """
        Predict the winner of a match.

        Parameters
        ----------
        red : str
            The name of the red character.
        blue : str
            The name of the blue character.

        Returns
        -------
        conf : float
            The confidence of the prediction.
        team : str
            The predicted winner.
        """

        # Get the token for each character
        red_token = db.get_token_from_name(red)
        blue_token = db.get_token_from_name(blue)

        # If either token is None, the character is not in the database.
        # This means we don't have any data on the character, so we can't predict the winner.
        if red_token is None or blue_token is None:
            return 0, random.choice(["red", "blue"])

        # Use the model to predict the winner
        input_data = np.array([[red_token, blue_token]], dtype=np.float32)
        pred = self.model.run(None, {"input": input_data})[0][0][0]

        # Convert the prediction to a confidence value
        conf = 1 / (1 + np.exp(-pred))

        # Convert the prediction to a team
        team = "red" if pred > 0 else "blue"

        return conf, team

    @staticmethod
    def calc_kelly_fractions(conf):
        p_winner = conf
        p_loser = 1 - conf
        odds_winner = 1 / 2
        odds_loser = 2

        def calc_kelly_fraction(p, odds):
            return (p * odds - (1 - p)) / odds

        kelly_fraction_winner = calc_kelly_fraction(p_winner, odds_winner)
        kelly_fraction_loser = calc_kelly_fraction(p_loser, odds_loser)

        return kelly_fraction_winner, kelly_fraction_loser

    @staticmethod
    def calc_suggested_wagers(k_winner, k_loser, balance, risk_adjustment=0.5):
        suggested_wager_winner = balance * k_winner * risk_adjustment
        suggested_wager_loser = balance * k_loser * risk_adjustment

        return suggested_wager_winner, suggested_wager_loser

    def get_wager(self, conf, balance, is_tournament):
        """
        Get the suggested wager for a match.

        Parameters
        ----------
        conf : float
            The confidence of the prediction.
        balance : int
            The current balance.
        is_tournament : bool
            Whether the match is a tournament match.

        Returns
        -------
        wager : int
            The suggested wager.
        bet_upset : bool
        """

        # If the confidence is 0, this means the model could not predict a winner
        # In this case, we bet a dollar
        if conf == 0:
            return 1, False

        # Calculate the kelly fractions and suggested wagers
        k_winner, k_loser = self.calc_kelly_fractions(conf)
        wager_winner, wager_loser = self.calc_suggested_wagers(k_winner, k_loser, balance)

        if k_winner > 0 and k_loser > 0:
            # If both kelly fractions are positive, bet on the team with the higher kelly fraction
            wager = wager_winner if k_winner > k_loser else wager_loser
            bet_upset = k_loser > k_winner
        elif k_winner > 0:
            # If only the kelly fraction for the winner is positive, bet on the winner
            wager = wager_winner
            bet_upset = False
        elif k_loser > 0:
            # If only the kelly fraction for the loser is positive, bet on the loser
            wager = wager_loser
            bet_upset = True
        else:
            # If both kelly fractions are negative, bet on the underdog
            wager = wager_loser if k_winner > k_loser else wager_winner
            bet_upset = k_winner <= k_loser

        # If our balance is too low, all in
        if balance < self.min_balance:
            return balance, bet_upset
        if balance < self.min_balance_tournament and is_tournament:
            return balance, bet_upset

        # Round the wager to the nearest integer and constrain it within [1, balance]
        wager = max(min(round(wager), balance), 1)
        return wager, bet_upset

    @staticmethod
    def int_to_money(money):
        """
        Convert a number to a string with a dollar sign and commas.

        Parameters
        ----------
        money : int
            The amount of money.

        Returns
        -------
        str
            The money as a string.
        """
        # Same width for up to 100 billion plus commas
        char_width = 15
        amount = round(money)
        dollar_sign = " $" if amount >= 0 else "-$"

        return f"{dollar_sign}{abs(amount):>{char_width},}"

    @staticmethod
    def money_to_int(money_str):
        """
        Convert a money string to an integer.

        Parameters
        ----------
        money_str : str
            The money string to convert.

        Returns
        -------
        int
            The money as an integer.
        """

        # Strip the dollar sign and commas
        raw_amount = re.sub(r"[$,]", "", money_str)

        # Convert to an integer
        amount = int(raw_amount)

        return amount


betting_module = BettingModule()