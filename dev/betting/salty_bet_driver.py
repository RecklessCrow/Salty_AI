import os
import re
import time

import dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

dotenv.load_dotenv()


class SaltyBetDriver:
    EXE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "geckodriver.exe")

    def __init__(self, headless=False):
        """
        Object to interact with SaltyBet
        :param headless: run web browser in headless mode
        """
        options = Options()

        if headless:
            options.add_argument("--headless")

        self.driver = webdriver.Firefox(
            executable_path=self.EXE_PATH,
            options=options
        )

        # login
        self.driver.get("https://www.saltybet.com/authenticate?signin=1")
        time.sleep(2)  # wait for page to load
        assert "Salty" in self.driver.title, 'Failed to load into website. Maybe saltybet.com is down?'

        username = self.driver.find_element(By.ID, "email")
        username.clear()
        username.send_keys(os.environ.get("SALTY_USERNAME"))

        password = self.driver.find_element(By.NAME, "pword")
        password.clear()
        password.send_keys(os.environ.get("SALTY_PASSWORD"))

        self.driver.find_element(By.CLASS_NAME, 'graybutton').click()

        time.sleep(2)  # wait for page to load
        assert "authenticate" not in self.driver.current_url, "Failed to login"

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

        try:
            level_url = self.driver.find_element(By.ID, "rank")
            level_url = level_url.find_element(By.CLASS_NAME, "levelimage").get_attribute("src")
            level = int(re.search("[0-9]+", level_url.split("/")[-1])[0])
            modifier = level * 25
        except:
            modifier = 0

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
        :return:
        """
        betting_text = self.driver.find_element(By.ID, "lastbet").text
        odds_text = betting_text.split("|")[-1].strip()

        if odds_text == "":
            return 0, 0

        red, blue = tuple(odds_text.split(":"))
        return float(red), float(blue)

    def get_fighters(self):
        """
        Gets the current characters of the red and blue teams
        :return:
        """
        red = self.driver.find_element(By.CLASS_NAME, "redtext").text
        blue = self.driver.find_element(By.CLASS_NAME, "bluetext").text

        if "|" in red:
            red = red.split('|')[1]
            blue = blue.split('|')[0]

        return red.strip(), blue.strip()

    def is_tournament(self):
        element = self.driver.find_element(By.ID, "footer-alert").text.lower()
        return "tournament" in element


if __name__ == '__main__':
    driver = SaltyBetDriver(headless=True)
    while True:
        print(driver.get_fighters())
        print(driver.get_odds())
        print(driver.get_balance())
        print(driver.get_game_state())
        print(driver.get_bailout(tournament=driver.is_tournament()))
        time.sleep(1)
