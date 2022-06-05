import os
import re
import time
from typing import Tuple

from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, \
    StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options


class SaltyBetGuiDriver:
    EXE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "", "../..", "geckodriver.exe")
    STATE_DICT = {
        "START": 0,
        "BETS_OPEN": 1,
        "BETS_CLOSED": 2,
        "PAYOUT": 3,
        "INVALID": 4
    }
    BASE_BAILOUT = 100
    TOURNAMENT_BASE_BAILOUT = 1000

    def __init__(self):
        """
        Initializes the driver
        """
        self.driver = None
        options = Options()
        options.add_argument("--headless")
        self.driver = webdriver.Firefox(executable_path=self.EXE_PATH, options=options)
        self.last_balance = 0

    def __del__(self):
        """
        Closes the driver
        """
        if self.driver is not None:
            self.driver.close()

    def login(self, username: str, password: str):
        """
        Logs in to saltybet.com
        :param username: The username
        :param password: The password
        :return: True if successful, False otherwise
        """
        self.driver.get("https://www.saltybet.com/authenticate?signin=1")

        time.sleep(1)
        assert "authenticate" in self.driver.current_url

        user = self.driver.find_element(By.ID, "email")
        user.clear()
        user.send_keys(username)

        pwrd = self.driver.find_element(By.NAME, "pword")
        pwrd.clear()
        pwrd.send_keys(password)

        self.driver.find_element(By.CLASS_NAME, 'graybutton').click()

        time.sleep(1)
        return "authenticate" not in self.driver.current_url

    def get_current_state(self) -> int:
        """
        Gets the current state of the match
        :return: The current state of the match (see STATE_DICT)
        """
        state_text = self.driver.find_element(By.ID, "betstatus").text.lower()

        if "open" in state_text:
            return self.STATE_DICT["BETS_OPEN"]

        elif "locked" in state_text:
            return self.STATE_DICT["BETS_CLOSED"]

        elif "payout" in state_text:
            return self.STATE_DICT["PAYOUT"]

        return self.STATE_DICT["INVALID"]

    def get_winner(self) -> str:
        """
        Gets the winner of the current matchup
        :return: The winner of the current matchup
        """
        state_text = self.driver.find_element(By.ID, "betstatus").text.lower()

        if "red" in state_text:
            return "red"

        if "blue" in state_text:
            return "blue"

        return ""

    def get_payout(self):
        """
        Gets the payout for the current match
        :return: The payout for the current match
        """
        payout = self.get_current_balance() - self.last_balance
        self.last_balance = self.get_current_balance()
        return payout

    def get_current_matchup(self) -> Tuple[str, str]:
        """
        Gets the current matchup
        :return: The red and blue teams
        """
        if self.last_balance == 0:
            self.last_balance = self.get_current_balance()

        try:
            red = self.driver.find_element(By.CLASS_NAME, "redtext").text
            blue = self.driver.find_element(By.CLASS_NAME, "bluetext").text
        except StaleElementReferenceException:
            time.sleep(1)
            return self.get_current_matchup()

        if "|" in red:
            red = red.split('|')[1]
            blue = blue.split('|')[0]

        return red.strip(), blue.strip()

    def get_bailout(self, tournament: bool) -> int:
        """
        Get the bailout amount for the player, based on level and if participating in a tournament
        :param tournament: if the current match is part of a tournament
        :return: bailout amount
        """
        try:
            level_url = self.driver.find_element(By.ID, "rank")
            level_url = level_url.find_element(By.CLASS_NAME, "levelimage").get_attribute("src")
            level = int(re.search(r"\d+", level_url.split("/")[-1])[0])
            modifier = level * 25

        except:
            modifier = 0

        if tournament:
            return self.TOURNAMENT_BASE_BAILOUT + modifier

        return self.BASE_BAILOUT + modifier

    def get_current_balance(self) -> int:
        """
        Gets the current balance
        :return: The current balance
        """
        betting_text = self.driver.find_element(By.ID, "balance")
        while not isinstance(betting_text, str) and betting_text == "":
            time.sleep(1)
            betting_text = self.driver.find_element(By.ID, "balance")

        balance = int(betting_text.text.replace(",", ""))

        if self.last_balance == 0:
            self.last_balance = balance

        return int(self.driver.find_element(By.ID, "balance").text.replace(",", ""))

    def get_current_odds(self) -> Tuple[float, float]:
        """
        Gets the odds and pots for the current matchup
        :return: The odds of the current matchup
        """

        # Wait for betting text to load
        betting_text = self.driver.find_element(By.ID, "lastbet").text
        while not isinstance(betting_text, str) and betting_text == "":
            time.sleep(1)
            betting_text = self.driver.find_element(By.ID, "lastbet").text

        # Get the odds
        odds = betting_text.split("|")[-1].strip().split(":")
        if len(odds) == 2:
            return float(odds[0]), float(odds[1])

        return self.get_current_odds()

    def get_current_pots(self) -> Tuple[int, int]:
        """
        Gets the current pots
        :return: The current pots
        """

        # Wait for pots text to load
        pots_text = self.driver.find_element(By.ID, "odds").text
        while not isinstance(pots_text, str) and pots_text == "":
            time.sleep(1)
            pots_text = self.driver.find_element(By.ID, "odds").text

        # Get the pots
        pots_text = pots_text.replace(",", "")
        red_pot, blue_pot = tuple(re.findall(r'(?<=\$)\d+', pots_text))

        return int(red_pot), int(blue_pot)

    def is_tournament(self) -> bool:
        """
        Checks if the current match is a tournament
        :return: True if the current match is a tournament, False otherwise
        """
        element = self.driver.find_element(By.ID, "footer-alert").text.lower()
        return "tournament" in element

    def place_bet(self, team: str, amount: int) -> bool:
        """
        Places a bet
        :param team: The team to bet on
        :param amount: The amount to bet
        :return: True if successful, False otherwise
        """

        if team not in ["red", "blue"]:
            return False

        if amount <= 0:
            return False

        try:
            self.driver.find_element(By.ID, "wager").send_keys(str(amount))
            self.driver.find_element(By.CLASS_NAME, f"betbutton{team}").click()
            self.driver.find_element(By.ID, "betconfirm")
            return True

        except ElementNotInteractableException:
            return False

        except NoSuchElementException:
            return False
