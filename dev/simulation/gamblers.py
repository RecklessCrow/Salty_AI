from abc import ABC

import numpy as np
import sigfig

from utils.salty_bet_driver import SaltyBetDriver


class Gambler(ABC):
    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        raise NotImplementedError

    @staticmethod
    def format_bet(bet_amount, balance) -> int:
        """
        Formats the bet amount to guarantee that the bet is valid and rounds to a number of significant figures.
        :param bet_amount: The amount to bet.
        :param balance: The balance of the gambler.
        :return: Amount to bet.
        """

        # Check that the bet amount is not zero or negative.
        bet_amount = int(max(bet_amount, 1))

        # Round the bet to a number of sig figs given by half the number of digits in the bet amount.
        bet_amount = sigfig.round(bet_amount, sigfigs=len(str(bet_amount)) // 2)

        # Check that the bet amount is not greater than the balance after rounding.
        bet_amount = min(bet_amount, balance)

        return int(bet_amount)


class AllIn(Gambler):
    """
    Gambler that bets all the balance all the time.
    """

    def __init__(self):
        """
        Initializes the gambler.
        """
        pass

    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        return self.format_bet(driver.get_balance(), driver.get_balance())


class ScaledConfidence(Gambler):
    """
    Gambler that bets a scaled amount of the balance based on the confidence.
    """

    def __init__(self):
        self.all_in_confidence = 0.9
        self.high_confidence = 0.75
        self.factor = 1 / 3

    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        is_tournament = driver.is_tournament()
        bailout = driver.get_bailout(is_tournament)
        balance = driver.get_balance()

        # Tournament betting rules
        if is_tournament:
            return 1

        # Bet all in if we're less than 2x bailout
        # Bet all in if we're above a certain confidence level
        if balance < 2 * bailout or confidence >= self.all_in_confidence:
            bet_amount = balance

        # Bet larger amount on matches with higher confidence
        elif confidence > self.high_confidence:
            bet_amount = balance * self.factor

        # Normal betting rules
        else:
            bet_amount = balance * confidence * self.factor

        return self.format_bet(bet_amount, balance)


class ExpScaledConfidence(Gambler):
    """
    Gambler that bets a scaled amount of the balance based on the confidence.
    """

    def __init__(self):
        super().__init__()

    @staticmethod
    def __get_tournament_parameters(balance, bailout):
        if balance < 2 * bailout:
            return 1.00, 0.45
        if balance < 3 * bailout:
            return 0.89, 0.42
        if balance < 4 * bailout:
            return 0.78, 0.38
        else:
            return 0.50, 0.29

    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        balance = driver.get_balance()

        confidence_slope = -0.12
        start_incline = 0.25
        ceiling_slope = -0.05
        ceiling = 1.0
        aggressive_factor = 3

        log_balance = min(np.log(balance), 13)
        confidence_bias = (log_balance - 5) * confidence_slope + (1.0 - start_incline)
        ceiling_factor = (log_balance - 5) * ceiling_slope + (ceiling / 2)
        ceiling_factor = max(0, ceiling_factor)

        if driver.is_tournament():
            confidence_bias, ceiling_factor = self.__get_tournament_parameters(balance, driver.get_bailout(True))

        confidence += confidence_bias
        bet_factor = confidence ** aggressive_factor
        x_crossover = ceiling_factor ** (1 / aggressive_factor)
        y_crossover = x_crossover ** aggressive_factor
        if confidence > x_crossover:
            bet_factor = -((x_crossover - (confidence - x_crossover)) ** aggressive_factor) + (y_crossover * 2)

        bet_amount = balance * bet_factor
        return self.format_bet(bet_amount, balance)


class ExpScaledConfidence2(Gambler):

    def __init__(self,
                 confidence_slope=None,
                 start_incline=None,
                 ceiling_slope=None,
                 ceiling=None,
                 bet_bias=0,
                 aggressive_factor=6):

        super().__init__()
        self.confidence_slope = confidence_slope
        self.start_incline = start_incline
        self.ceiling_slope = ceiling_slope
        self.ceiling = ceiling
        self.bet_bias = bet_bias
        self.aggressive_factor = aggressive_factor

    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        balance = driver.get_balance()

        log_balance = min(np.log(balance), 13)  #
        confidence_bias = (log_balance - 5) * self.confidence_slope + (1.0 - self.start_incline)
        ceiling_factor = (log_balance - 5) * self.ceiling_slope + (self.ceiling / 2)
        ceiling_factor = max(0, ceiling_factor)
        bet_bias = self.bet_bias
        aggressive_factor = self.aggressive_factor

        confidence = (confidence - 0.5) * 2

        confidence += confidence_bias
        bet_factor = confidence ** aggressive_factor
        x_crossover = ceiling_factor ** (1 / aggressive_factor)
        y_crossover = x_crossover ** aggressive_factor
        if confidence > x_crossover:
            bet_factor = -((x_crossover - (confidence - x_crossover)) ** aggressive_factor) + (y_crossover * 2)

        # bet_factor += bet_bias
        bet_factor += bet_bias
        bet_factor = max(min(bet_factor, 1), 0)
        bet_amount = balance * bet_factor
        bet_amount = min(bet_amount, balance)

        return bet_amount


class LinearScaledConfidence(Gambler):

    def __init__(self,
                 confidence_slope=None,
                 bet_bias=None,
                 balance_slope=None,
                 balance_bias=None):

        super().__init__()
        self.confidence_slope = confidence_slope
        self.bet_bias = bet_bias
        self.balance_slope = balance_slope
        self.balance_bias = balance_bias

    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        balance = driver.get_balance()
        confidence = (confidence - 0.5) * 2

        bet_factor = (confidence * self.confidence_slope) + self.bet_bias

        bet_factor = max(min(bet_factor, 1), 0)
        bet_amount = balance * bet_factor
        return bet_amount

GAMBLER_ID_DICT = {
    0: AllIn,
    1: ScaledConfidence,
    2: ExpScaledConfidence,
}
