import os
import re
import sys

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

load_dotenv()


class SaltyBetDriver:
    def __init__(self, headless=False):
        """
        Object to interact with SaltyBet
        :param headless: run web browser in headless mode
        """
        options = Options()

        if headless:
            options.add_argument("--headless")

        self.driver = webdriver.Firefox(
            service=Service(executable_path=GeckoDriverManager().install()),
            options=options
        )

        # login
        self.driver.get("https://www.saltybet.com/authenticate?signin=1")
        try:
            assert "Salty" in self.driver.title
        except AssertionError:
            print('Failed to load into website. Maybe saltybet.com is down?')
            sys.exit()

        username = self.driver.find_element(By.ID, "email")
        username.clear()
        username.send_keys(os.getenv("email"))

        password = self.driver.find_element(By.NAME, "pword")
        password.clear()
        password.send_keys(os.getenv("password"))

        self.driver.find_element(By.CLASS_NAME, 'graybutton').click()

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

    def get_balance(self):
        """
        Get the current balance of the player
        :return: salt
        """
        return int(self.driver.find_element(By.ID, "balance").text.replace(",", ""))

    def get_game_state(self):
        """
        Get the current state of the game
        :return: state string
        """
        return self.driver.find_element(By.ID, 'betstatus').text.lower()

    def bet(self, amount: int, team: str):
        """
        Bet some amount on a team
        :param amount: Amount to bet on the team
        :param team: Team to bet on. Either 'red' or 'blue'
        :return:
        """

        assert team in ["red", "blue"]

        self.driver.find_element(By.ID, "wager").send_keys(str(amount))
        self.driver.find_element(By.CLASS_NAME, f"betbutton{team}").click()

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
        tournament_text = self.driver.find_element(By.ID, "footer-alert").text.lower()
        return "bracket" in tournament_text or \
               "final" in tournament_text or \
               "tournament" in tournament_text


if __name__ == '__main__':
    driver = SaltyBetDriver(headless=True)
