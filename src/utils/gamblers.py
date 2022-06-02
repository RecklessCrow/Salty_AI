from abc import ABC

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
        # bet_amount = sigfig.round(bet_amount, sigfigs=len(str(bet_amount)) // 2)

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
    def __get_parameters(balance):
        if balance < 1_000:
            return 0.725, 0.36
        if balance < 10_000:
            return 0.33, 0.24
        if balance < 100_000:
            return 0.175, 0.187
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

    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
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
        bet_amount = balance * bet_factor
        return self.format_bet(bet_amount, balance)


class NumMatchWeighted(Gambler):
    """
    Gambler that bets a scaled amount of the balance based on the confidence and number of seen match ups.
    """

    BALANCE_CAP = 100_000
    HIGH_CONFIDENCE = 0.8
    ALL_IN_CONFIDENCE = 0.9
    MAX_BET = 1_000_000
    MAX_NORMAL_BET = 5_000

    from utils.database_handler import MatchDatabaseHandler
    DATABASE = MatchDatabaseHandler()

    def __init__(self):
        pass

    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
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

        return self.format_bet(bet_amount, balance)


GAMBLER_ID_DICT = {
    0: AllIn,
    1: NumMatchWeighted,
    2: ScaledConfidence,
    3: ExpScaledConfidence,
}
