import time
import numpy as np

from app.utils.settings import settings


def await_next_state(driver, last_state):
    """
    Awaits the next state of SaltyBet. Possible states are START, BETS_OPEN, BETS_CLOSED, PAYOUT.

    Parameters
    ----------
    driver : SaltyBetDriver
        Salty bet driver to interface with website.
    last_state : int
        State enum of the last known state.

    Returns
    -------
    state : int
        New state of the game.
    """

    state = last_state

    # Base case where the app was just started. Wait for a new match to start.
    if last_state == settings.STATES["START"]:
        while True:
            if driver.get_game_state() == settings.STATES["BETS_OPEN"]:
                return settings.STATES["BETS_OPEN"]
            time.sleep(settings.SLEEP_TIME)

    while state == last_state:
        state = driver.get_game_state()
        time.sleep(settings.SLEEP_TIME)

        if state is None:
            state = last_state

    return state


def softmax(x: np.array) -> np.array:
    """
    Compute softmax values for each sets of scores in x.

    Parameters
    ----------
    x : np.array
        Array of logits.

    Returns
    -------
    np.array
        Softmaxed values.

    """
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)  # only difference


def int_to_money_str(amount) -> str:
    """
    Transforms an integer into a money string. Will maintain equal spacing for values less than or equal to
    999,999,999,999. This function follows the formatting found on excell for accounting. As in, negative values are
    wrapped in parenthesis.

    Examples
    --------
    >>> int_to_money_str(100)
    ' $          100'

    >>> int_to_money_str(-100)
    '($          100)'

    # Floating values are rounded

    >>> int_to_money_str(100.4)
    ' $          100'

    Parameters
    ----------
    amount : int or float
        Number to transform into a money string.

    Returns
    -------
    money_str : str
        Money string with accounting formatting.
    """
    char_width = 13  # 100 billion spacing

    amount = round(amount)

    if amount < 0:
        return f"(${np.abs(amount):>{char_width},})"

    return f" ${amount:>{char_width},}"


def calc_bet(balance: int, conf: float) -> int:
    """
    Calculates the amount to bet based on the current balance and the model's confidence.

    Parameters
    ----------
    balance : int
        Current amount of money in our balance.
    conf : float
        Confidence of our model for the likelihood of a positive outcome.

    Returns
    -------
    bet_amount : int
        Amount to bet on this match.
    """
    confidence_slope = -0.12
    start_incline = 0.25
    ceiling_slope = -0.05
    ceiling = 1.0
    aggressive_factor = 3

    log_balance = min(np.log(balance), 13)
    confidence_bias = (log_balance - 5) * confidence_slope + (1.0 - start_incline)
    ceiling_factor = (log_balance - 5) * ceiling_slope + (ceiling / 2)
    ceiling_factor = max(0, ceiling_factor)

    conf += confidence_bias
    bet_factor = conf ** aggressive_factor
    x_crossover = ceiling_factor ** (1 / aggressive_factor)
    y_crossover = x_crossover ** aggressive_factor
    if conf > x_crossover:
        bet_factor = -((x_crossover - (conf - x_crossover)) ** aggressive_factor) + (y_crossover * 2)

    bet_factor = max(min(bet_factor, 1), 0)
    bet_amount = balance * bet_factor
    return int(bet_amount)
