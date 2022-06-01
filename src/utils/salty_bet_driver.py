import re
import time
from abc import ABC

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options


class SaltyBetDriver(ABC):
    def __init__(self, headless=False):
        """
        Object to interact with SaltyBet
        :param headless: run web browser in headless mode
        """
        options = Options()

        if headless:
            options.add_argument("--headless")

        self.driver = webdriver.Firefox(options=options)

    def __del__(self):
        self.driver.close()

    def get_bailout(self, tournament):
        """
        Get the bailout amount for the player, based on level and if participating in a tournament
        :param tournament: if the current match is part of a tournament
        :return: bailout amount
        """
        base_bailout = 100
        tournament_base_bailout = 1000

        level_url = self.driver.find_element(By.ID, "rank")
        level_url = level_url.find_element(By.CLASS_NAME, "levelimage").get_attribute("src")
        level = int(re.search("[0-9]+", level_url.split("/")[-1])[0])

        modifier = level * 25

        if tournament:
            return tournament_base_bailout + modifier

        return base_bailout + modifier

    def get_balance(self) -> int:
        """
        Get the current balance of the player
        :return: salt
        """
        balance_text = self.driver.find_element(By.ID, "balance").text

        # while balance_text == "" or not isinstance(balance_text, str):
        #     balance_text = self.driver.find_element(By.ID, "balance").text
        #     time.sleep(1)

        balance = int(balance_text.replace(",", ""))
        return balance

    def get_game_state(self):
        """
        Get the current state of the game
        :return: state string
        """
        state_text = self.driver.find_element(By.ID, "betstatus").text

        # while state_text == "" or not isinstance(state_text, str):
        #     state_text = self.driver.find_element(By.ID, "betstatus").text
        #     time.sleep(1)

        return state_text

    def place_bet(self, amount: int, team: str):
        """
        Bet some amount on a team
        :param amount: Amount to bet on the team
        :param team: Team to bet on. Either 'red' or 'blue'
        :return:
        """

        assert team in ["red", "blue"]

        self.driver.find_element(By.ID, "wager").send_keys(str(amount))
        self.driver.find_element(By.CLASS_NAME, f"betbutton{team}").click()

    def get_odds(self):
        """
        Get the odds of the current match
        :return: Betting odds of the current match
        """
        betting_text = self.driver.find_element(By.ID, "lastbet").text

        odds_text = betting_text.split("|")[-1].strip()
        red, blue = tuple(odds_text.split(":"))
        return float(red), float(blue)

    def get_fighters(self):
        """
        Gets the current characters of the red and blue teams
        :return:
        """
        try:
            red = self.driver.find_element(By.CLASS_NAME, "redtext").text
            blue = self.driver.find_element(By.CLASS_NAME, "bluetext").text
        except StaleElementReferenceException:
            return

        if "|" in red:
            red = red.split('|')[1]
            blue = blue.split('|')[0]

        return red.strip(), blue.strip()

    def is_tournament(self):
        tournament_text = self.driver.find_element(By.ID, "balancewrapper").text.lower()

        while tournament_text == "":
            tournament_text = self.driver.find_element(By.ID, "balancewrapper").text.lower()
            time.sleep(1)

        return "tournament" in tournament_text


class HomepageDriver(SaltyBetDriver):
    def __init__(self):
        """
        Object to interact with SaltyBet
        """
        super().__init__(headless=True)

        # Load into the website
        self.driver.get("https://www.saltybet.com")
        assert "Salty Bet" == self.driver.title, 'Failed to load into website. Maybe saltybet.com is down?'


class ModelDriver(SaltyBetDriver):
    def __init__(self, username, password):
        """
        Object to interact with SaltyBet
        """
        super().__init__(headless=True)

        # Load into the website
        self.driver.get("https://www.saltybet.com/authenticate?signin=1")
        assert "Salty Bet" == self.driver.title, 'Failed to load into website. Maybe saltybet.com is down?'

        # Login
        username_element = self.driver.find_element(By.ID, "email")
        username_element.clear()
        username_element.send_keys(username)

        password_element = self.driver.find_element(By.NAME, "pword")
        password_element.clear()
        password_element.send_keys(password)

        self.driver.find_element(By.CLASS_NAME, 'graybutton').click()

        # Check if we are logged in
        assert "authenticate" not in self.driver.current_url.lower(), \
            "Could not successfully login using given credentials. "
