from abc import ABC, abstractmethod

import sigfig
from base.base_database_handler import DATABASE
from base.base_salty_bet_driver import SaltyBetDriver


class Gambler(ABC):
    @abstractmethod
    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        pass

    def bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        """
        Places a bet on the given team.
        :param confidence: Confidence of the model.
        :param driver: Object that interacts with the website.
        :param team: Team to bet on.
        :return:
        """
        bet_amount = self.calculate_bet(confidence, driver)
        bet_amount = max(int(bet_amount), 1)
        return bet_amount

    @staticmethod
    def on_tournament(confidence: float, driver: SaltyBetDriver) -> int:
        balance = driver.get_balance()
        bet_amount = balance * confidence

        if bet_amount < 4 * driver.get_bailout(True):
            bet_amount = balance

        return bet_amount


class AllIn(Gambler):
    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        return driver.get_balance()


class ScaledConfidence(Gambler):
    def __init__(self):
        self.all_in_confidence = 0.9
        self.high_confidence = 0.75
        self.factor = 1/3

    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        is_tournament = driver.is_tournament()
        bailout = driver.get_bailout(is_tournament)
        balance = driver.get_balance()

        # Tournament betting rules
        if is_tournament:
            return self.on_tournament(confidence, driver)

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

        bet_amount = int(bet_amount)
        bet_amount = sigfig.round(bet_amount, sigfigs=len(str(bet_amount)) // 2)

        if bet_amount > balance:
            bet_amount = balance

        return bet_amount


class ExpScaledConfidence(ScaledConfidence):
    def __init__(self):
        super().__init__()

    @staticmethod
    def __get_coff(balance):
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

    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        is_tournament = driver.is_tournament()
        bailout = driver.get_bailout(is_tournament)
        balance = driver.get_balance()

        if is_tournament:
            return super().on_tournament(confidence, driver)

        # scale balance exponentially based on confidence
        conf_bias, factor = self.__get_coff(balance)
        bet_bias = 0.03  # minimum bet percentage
        base = 8  # ramp up bet percentage

        confidence += conf_bias
        bet_factor = confidence ** base
        x_crossover = factor ** (1 / base)
        y_crossover = x_crossover ** base
        if confidence > x_crossover:
            bet_factor = -((x_crossover - (confidence - x_crossover)) ** base) + (y_crossover * 2)

        bet_factor += bet_bias

        bet_amount = int(bet_factor * balance)
        bet_amount = sigfig.round(bet_amount, sigfigs=len(str(bet_amount)) // 2)

        return bet_amount


class NumMatchWeighted(Gambler):
    BALANCE_CAP = 100_000
    HIGH_CONFIDENCE = 0.8
    ALL_IN_CONFIDENCE = 0.9
    MAX_BET = 1_000_000
    MAX_NORMAL_BET = 5_000

    def calculate_bet(self, confidence: float, driver: SaltyBetDriver) -> int:
        r, b = driver.get_fighters()
        matchup_count = DATABASE.get_matchup_count(r, b)
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
