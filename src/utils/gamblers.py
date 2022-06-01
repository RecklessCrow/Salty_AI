from abc import ABC, abstractmethod

import sigfig

from database_handler import MatchDatabaseHandler
from salty_bet_driver import SaltyBetDriver


class Gambler(ABC):
    @abstractmethod
    def __calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        pass

    def get_bet_amount(self, confidence: float, driver: SaltyBetDriver) -> int:
        """
        Gets the amount to bet based on the confidence and performs necessary checks.
        :param confidence: Confidence of the utils.
        :param driver: Object that interacts with the website.
        :return: Amount to bet.
        """
        # Calculate the bet amount.
        bet_amount = self.__calculate_bet(confidence, driver)

        # Check that the bet amount is not zero or negative.
        bet_amount = max(bet_amount, 1)

        # Round the bet to a number of sig figs given by half the number of digits in the bet amount.
        bet_amount = sigfig.round(bet_amount, sigfigs=len(str(bet_amount)) // 2)

        # Check that the bet amount is not greater than the balance after rounding.
        bet_amount = min(bet_amount, driver.get_balance())

        return int(bet_amount)


class AllIn(Gambler):
    def __calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        return driver.get_balance()


class ScaledConfidence(Gambler):
    def __init__(self):
        self.all_in_confidence = 0.9
        self.high_confidence = 0.75
        self.factor = 1/3

    def __calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
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

        return bet_amount


class ExpScaledConfidence(ScaledConfidence):
    def __init__(self):
        super().__init__()

    @staticmethod
    def __get_parameters(balance):
        if balance < 1_000:
            return 1.00, 0.45
        if balance < 5_000:
            return 0.89, 0.42
        if balance < 10_000:
            return 0.78, 0.38
        if balance < 50_000:
            return 0.50, 0.29
        if balance < 100_000:
            return 0.28, 0.22
        if balance < 1_000_000:
            return 0.01, 0.14
        else:
            return -0.1, 0.10

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

    def __calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        balance = driver.get_balance()

        if driver.is_tournament():
            conf_bias, factor = self.__get_tournament_parameters(balance, driver.get_bailout(True))
        else:
            conf_bias, factor = self.__get_parameters(balance)

        # scale balance exponentially based on confidence
        bet_bias = 0.03  # minimum bet percentage
        base = 8  # ramp up bet percentage

        confidence += conf_bias
        bet_factor = confidence ** base
        x_crossover = factor ** (1 / base)
        y_crossover = x_crossover ** base
        if confidence > x_crossover:
            bet_factor = -((x_crossover - (confidence - x_crossover)) ** base) + (y_crossover * 2)

        bet_factor += bet_bias

        return bet_factor * balance


class NumMatchWeighted(Gambler):
    BALANCE_CAP = 100_000
    HIGH_CONFIDENCE = 0.8
    ALL_IN_CONFIDENCE = 0.9
    MAX_BET = 1_000_000
    MAX_NORMAL_BET = 5_000
    DATABASE = MatchDatabaseHandler("matches")

    def __calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        r, b = driver.get_fighters()
        matchup_count = self.DATABASE.get_matchup_count(r, b)
        print("Matchup count:", matchup_count)
        matchup_rate = lambda count_seen: 1 - ((2 - count_seen) * 0.1)
        matchup_weight = min(matchup_rate(matchup_count), 1.0)
        confidence = confidence * matchup_weight

        is_tournament = driver.is_tournament()
        bailout = driver.get_bailout(is_tournament)
        balance = driver.get_balance()

        # Bet all in if we're less than 2x bailout
        if balance < 2 * bailout:
            bet_amount = balance

        # Bet all in if we're above a certain confidence level
        elif confidence > self.ALL_IN_CONFIDENCE:
            bet_amount = balance if balance < 1e6 else (balance * confidence) / 2

        elif confidence > self.HIGH_CONFIDENCE:
            bet_amount = (balance * confidence) / 4

        else:  # normal betting rules
            if balance < self.BALANCE_CAP:
                bet_amount = balance * (confidence / 2)
            else:
                bet_amount = balance * 0.05

            bet_amount = min(self.MAX_NORMAL_BET, bet_amount)

        bet_amount = int(bet_amount)
        bet_amount = sigfig.round(bet_amount, sigfigs=len(str(bet_amount)) // 2)

        if bet_amount > balance:
            bet_amount = balance

        return bet_amount


GAMBLER_ID_DICT = {
    0: AllIn(),
    1: NumMatchWeighted(),
    2: ScaledConfidence(),
    3: ExpScaledConfidence(),
}
