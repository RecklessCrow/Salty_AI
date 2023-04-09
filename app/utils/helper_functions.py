import time

import numpy as np

from utils.settings import settings, States


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
    if last_state == States.START:
        while True:
            if driver.get_game_state() == States.BETS_OPEN:
                return States.BETS_OPEN
            time.sleep(settings.WAIT_TIME)

    while state == last_state:
        state = driver.get_game_state()
        time.sleep(settings.WAIT_TIME)

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

    # Set the maximum bet as a fraction of our balance (e.g., 10%)
    max_bet_fraction = 0.5
    max_bet = max_bet_fraction * balance

    # Calculate the optimal bet size based on the confidence level
    bet = max_bet * (2 * confidence - 1)

    # Round the bet to the nearest integer (you can modify this as needed)
    bet = round(bet)

    # Make sure the bet is within our balance limits
    bet = min(bet, max_bet)  # don't bet more than we have or can afford
    bet = max(bet, 750 - balance)  # don't bet less than what we need to reach the minimum balance

    return bet
