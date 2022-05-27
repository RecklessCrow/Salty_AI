from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options


class SaltyBetDriver:
    def __init__(self):
        """
        Object to interact with SaltyBet
        :param headless: run web browser in headless mode
        """
        options = Options()
        options.add_argument("--headless")

        self.driver = webdriver.Firefox(
            options=options
        )

        # login
        self.driver.get("https://www.saltybet.com")

        # Check if successful
        assert "salty" in self.driver.title.lower()

    def __del__(self):
        self.driver.close()

    def get_game_state(self):
        """
        Get the current state of the game
        :return: state string
        """
        return self.driver.find_element(By.ID, 'betstatus').text.lower()

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
