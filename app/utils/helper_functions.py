import time

import numpy as np

from utils.settings import settings


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


def sigmoid(x: float):
    return 1 / (1 + np.exp(-x))


def convert_to_money_str(amount) -> str:
    """
    Transforms an integer into a money string. Will maintain equal spacing for values less than or equal to
    999,999,999,999. This function follows the formatting found on excell for accounting. As in, negative values are
    wrapped in parenthesis.

    Examples
    --------
    >>> convert_to_money_str(1000)
    ' $        1,000'

    >>> convert_to_money_str(-1000)
    '($        1,000)'

    # Floating values are rounded

    >>> convert_to_money_str(1000.4)
    ' $        1,000'

    Parameters
    ----------
    amount : int or float
        Number to transform into a money string.

    Returns
    -------
    money_str : str
        Money string with accounting formatting.
    """
    char_width = 15  # 100 billion spacing

    amount = round(amount)

    if amount < 0:
        return f"(${np.abs(amount):>{char_width},})"

    return f" ${amount:>{char_width},}"


def calc_bet(balance: int, confidence: float) -> int:
    """
    Calculates the amount to bet based on the current balance and the development's confidence.

    Parameters
    ----------
    balance : int
        Current amount of money in our balance.
    confidence : float
        Confidence of our development for the likelihood of a positive outcome.

    Returns
    -------
    bet_amount : int
        Amount to bet on this match.
    """
    # Calculate the Kelly criterion percentage
    kelly_pct = (confidence - (1 - confidence)) / confidence
    # Limit the Kelly percentage to a maximum of 50% to avoid excessive risk
    kelly_pct = min(kelly_pct, 0.5)
    # Calculate the optimal bet amount based on the Kelly percentage and current balance
    bet_amount = balance * kelly_pct
    # Use a value betting approach to adjust the bet amount based on the confidence level
    if confidence < 0.6:
        bet_amount *= 0.5
    elif confidence < 0.7:
        bet_amount *= 0.75
    elif confidence < 0.8:
        bet_amount *= 1.25
    else:
        bet_amount *= 1.5
    # Round the bet amount to the nearest whole number
    bet_amount = round(bet_amount)
    # Ensure that the bet amount is not greater than the current balance
    bet_amount = min(bet_amount, balance)
    # Return the bet amount
    return bet_amount
