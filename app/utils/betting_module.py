import logging
import re

import numpy as np
import onnxruntime as ort
from onnxruntime.capi.onnxruntime_pybind11_state import InvalidArgument

from database.interface import db
from utils.config import config


class BettingModule:

    def __init__(self):
        self.logger = logging.getLogger("BettingModule")
        self.logger.info("Initializing betting module")

        # Minimum balance we need before we stop going all in
        self.min_balance = 10_000
        self.min_balance_tournament = 2 * self.min_balance

        # Risk adjustment factors
        self.max_risk = 0.30  # Maximum risk adjustment
        self.min_risk = 0.01  # Minimum risk adjustment
        self.threshold_balance = 100_000_000  # Balance where risk adjustment becomes minimal

        # Load the model
        self.model = ort.InferenceSession(str(config.MODEL_PATH))

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
        red : float
            The probability of the red character winning.
        blue : float
            The probability of the blue character winning.
        """

        # Get the token for each character
        red_token = db.get_token_from_name(red)
        blue_token = db.get_token_from_name(blue)

        # If either token is None, the character is not in the database.
        # This means we don't have any data on the character, so we can't predict the winner.
        if red_token is None or blue_token is None:
            return -1, -1

        # Use the model to predict the winner
        try:
            input_data = np.array([[red_token, blue_token]], dtype=np.int64)
            pred = self.model.run(None, {"input": input_data})[0][0]
            softmax = np.exp(pred) / np.sum(np.exp(pred))
        except InvalidArgument:
            # If the model throws an InvalidArgument exception, this means the model was not
            # trained on one of the characters.
            self.logger.error(f"Invalid argument for {red} vs {blue}")
            return -1, -1

        return softmax

    @staticmethod
    def calc_kelly_criterion(p, odds):
        """
        Calculate the kelly criterion for a match.

        Parameters
        ----------
        p : float
            The probability of winning.
        odds : float
            The decimal odds for the prediction.

        Returns
        -------
        float
            The kelly criterion.
        """
        return round(p - ((1 - p) / odds), 3)

    def get_wager(self, red, blue, balance, is_tournament):
        """
        Get the suggested wager for a match.

        Parameters
        ----------
        red : str
            The name of the red character.
        blue : str
            The name of the blue character.
        balance : int
            The current balance.
        is_tournament : bool
            Whether the match is a tournament match.
        """
        # Get the prediction
        p_red, p_blu = self.predict_winner(red, blue)
        self.logger.debug(f"Prediction: {p_red} : {p_blu}")
        # p_red, p_blu = (0.7, 0.3) if p_red > p_blu else (0.3, 0.7)

        # If the confidence is 0, this means the model could not predict a winner
        # In this case, we bet a dollar
        if p_red == -1:
            return 1, "red"

        # Try to get the odds from the database
        odds_red, odds_blu = db.get_matchup_odds(red, blue)

        # Default odds are 2.2 : 1 in favor of the character with the higher prediction
        if odds_red is None or odds_blu is None:
            if p_red > p_blu:
                odds_red, odds_blu = 2.2, 1
            else:
                odds_red, odds_blu = 1, 2.2
        self.logger.debug(f"Odds: {odds_red} : {odds_blu}")

        # Convert the odds to decimal
        if odds_red == 1:
            odds_red = odds_blu + 1
            odds_blu = (1 / odds_blu) + 1
        else:
            odds_blu = odds_red + 1
            odds_red = (1 / odds_red) + 1
        self.logger.debug(f"Decimal odds: {odds_red} : {odds_blu}")

        # Calculate the kelly criterion
        k_red = self.calc_kelly_criterion(p_red, odds_red)
        k_blu = self.calc_kelly_criterion(p_blu, odds_blu)
        self.logger.debug(f"Kelly: {k_red} : {k_blu}")

        # Bet on the character with the higher kelly criterion
        team = "red" if k_red > k_blu else "blue"

        # If our balance is too low, all in
        if balance < self.min_balance:
            return balance, team
        if balance < self.min_balance_tournament and is_tournament:
            return balance, team

        # Percent of balance to wager. This approaches 0 as our balance approaches infinity.
        risk_adjustment = self.max_risk - (self.max_risk - self.min_risk) * (balance / self.threshold_balance)
        risk_adjustment = round(risk_adjustment, 3)
        risk_adjustment = max(risk_adjustment, self.min_risk)
        risk_adjustment = min(risk_adjustment, self.max_risk)
        self.logger.debug(f"Risk adjustment: {risk_adjustment}")

        # Calculate the wager
        p_balance = balance * risk_adjustment
        wager = p_balance * k_red if team == "red" else p_balance * k_blu

        # Make sure the wager is between 1 and the balance
        wager = min(max(wager, 1), balance)
        wager = int(wager)

        return wager, team

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