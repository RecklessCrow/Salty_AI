import json
import logging
import os
import random
import re

import numpy as np
import onnxruntime as ort

from app.utils.settings import settings

# Load the model
if settings.MODEL_DIR:
    model = ort.InferenceSession(os.path.join(settings.MODEL_DIR, 'model.onnx'))
    with open(os.path.join(settings.MODEL_DIR, 'vocab.json')) as f:
        characters = json.load(f)
else:
    raise ValueError("No model directory specified.")


def predict_winner(red, blue):
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

    # Convert the characters to indices
    try:
        red_idx = characters[red]
        blue_idx = characters[blue]

    except KeyError:
        # Find out which character is missing
        if red not in characters:
            logging.warning(f"Unknown character: {red}")

        if blue not in characters:
            logging.warning(f"Unknown character: {blue}")

        # If we don't have a character in our vocab, just return a random prediction
        return -1, random.choice(["red", "blue"])

    model_input = np.array([[red_idx, blue_idx]]).astype(np.int64)
    output = model.run(None, {'input': model_input})[0][0]

    # Softmax the output
    output = np.exp(output) / np.sum(np.exp(output), axis=0)

    # Get the predicted winner
    pred = np.argmax(output)
    team = "red" if pred == 0 else "blue"

    # Get the confidence
    conf = float(output[pred])

    return conf, team


def calculate_bet(balance, confidence, is_tournament):
    """
    Calculate the amount to bet based on the confidence and balance.

    Parameters
    ----------
    balance : int
        The current balance.
    confidence : float
        The confidence in the prediction. Should be between 0.5 and 1.
    is_tournament : bool
        Whether we're in a tournament.

    Returns
    -------
    bet_amount : int
        The amount to bet.
    """
    if is_tournament:
        # Set the minimum bet amount to the tournament buy-in
        min_bet = 1250

        # Determine the risk level based on the confidence value
        risk = np.exp(3 * (confidence - 1))

        # Calculate the maximum proportion of the balance we want to bet based on the balance
        max_proportion = 1

    else:
        # Set the minimum bet amount to regular buy-in
        min_bet = 750

        # Determine the risk level based on the confidence value
        risk = np.exp(6 * (confidence - 1)) / 1.5

        # Calculate the maximum proportion of the balance we want to bet based on the balance
        max_proportion = 1 / (balance / 1000)

    # Calculate the bet amount as a percentage of the balance
    bet_amount = round(balance * risk)

    # Limit the bet amount to the maximum proportion of the balance we want to bet
    bet_amount = min(bet_amount, round(balance * max_proportion))

    # Limit the bet amount to the available balance and the minimum bet amount
    bet_amount = max(bet_amount, min_bet)
    bet_amount = min(bet_amount, balance)

    return bet_amount



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


def update_json(data):
    """
    Update the data for the json endpoint.
    """

    with open(settings.JSON_PATH, 'w') as j:
        json.dump(data, j)
