import re
import time

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from app.utils.settings import settings
from app.utils.utils import STATES


class SaltyBetDriver:
    def __init__(self):
        """

        """

        self.last_balance = 0
        self.last_t_balance = 0

        self.winnings = 0
        self.t_winnings = 0

        options = Options()
        options.add_argument("--headless")

        self.driver = webdriver.Firefox(options=options)

        # Load into the website
        self.driver.get("https://www.saltybet.com/authenticate?signin=1")
        time.sleep(1)
        if "Salty Bet" != self.driver.title:
            raise RuntimeError('Failed to load into website. Maybe saltybet.com is down?')

        # Login
        username_element = self.driver.find_element(By.ID, "email")
        username_element.clear()
        username_element.send_keys(settings.SALTYBET_USERNAME)

        password_element = self.driver.find_element(By.NAME, "pword")
        password_element.clear()
        password_element.send_keys(settings.SALTYBET_PASSWORD)

        self.driver.find_element(By.CLASS_NAME, 'graybutton').click()

        # Check if we are logged in
        time.sleep(1)
        if "authenticate" in self.driver.current_url.lower():
            raise RuntimeError('Failed to login. Wrong username or password?')

        # Load into the website
        self.driver.get("https://www.saltybet.com")

        # Check that we loaded in correctly
        time.sleep(1)
        if "Salty Bet" != self.driver.title:
            raise RuntimeError('Failed to load website. Maybe saltybet.com is down?')

    def __del__(self):
        """
        Close the driver on delete.
        """
        self.driver.close()

    def _get_element_by_id(self, value: str) -> str:
        """


        Parameters
        ----------
        value

        Returns
        -------

        """
        text = self.driver.find_element(By.ID, value).text

        # Got invalid text? Wait until state is valid.
        while not isinstance(text, str) or text == "":
            text = self.driver.find_element(By.ID, value).text
            time.sleep(1)

        return text

    def get_game_state(self):
        """
        Gets the current state of the game.

        Returns
        -------
        state : int or None
            Enumerated state or None if state could not be decoded.
        """
        encoded_state = self._get_element_by_id("betstatus").lower()

        if "locked" in encoded_state:
            return STATES["BETS_CLOSED"]

        if "open" in encoded_state:
            return STATES["BETS_OPEN"]

        if "payout" in encoded_state:
            return STATES["PAYOUT"]

        return None

    def place_bet(self, amount: int, team: str):
        """
        Bet some amount on a team
        :param amount: Amount to bet on the team
        :param team: Team to bet on. Either 'red' or 'blue'
        :return:
        """

        if team not in ["red", "blue"]:
            raise ValueError("Team must be either 'red' or 'blue'")

        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        time.sleep(0.5)
        wager = self.driver.find_element(By.ID, "wager")
        wager.click()
        wager.clear()
        wager.click()
        wager.send_keys(str(amount))

        time.sleep(0.5)
        self.driver.find_element(By.CLASS_NAME, f"betbutton{team}").click()

    def get_odds(self):
        """
        Get the odds of the current match
        :return: Betting odds of the current match
        """
        betting_text = self.driver.find_element(By.ID, "lastbet").text

        while not isinstance(betting_text, str) or betting_text == "":
            betting_text = self.driver.find_element(By.ID, "lastbet").text
            time.sleep(1)

        odds_text = betting_text.split("|")[-1].strip()
        red, blue = tuple(odds_text.split(":"))
        return float(red), float(blue)

    def get_fighters(self) -> (str, str):
        """
        Gets the current characters of the red and blue teams
        :return:
        """
        try:
            red = self.driver.find_element(By.CLASS_NAME, "redtext").text
            blue = self.driver.find_element(By.CLASS_NAME, "bluetext").text
        except StaleElementReferenceException:
            return None, None

        if "|" in red:
            red = red.split('|')[1]
            blue = blue.split('|')[0]

        return red.strip(), blue.strip()

    def get_current_balance(self) -> int:
        """
        Gets the current balance
        :return: The current balance
        """

        betting_text = self.driver.find_element(By.ID, "balance").text
        while not isinstance(betting_text, str) or betting_text == "":
            time.sleep(1)
            betting_text = self.driver.find_element(By.ID, "balance").text

        balance = int(betting_text.replace(",", ""))

        if self.last_balance == 0:
            self.last_balance = balance

        return int(self.driver.find_element(By.ID, "balance").text.replace(",", ""))

    def get_payout(self) -> int:
        """
        Gets the payout for the current match
        :return: The payout for the current match
        """
        balance = self.get_current_balance()

        if self.is_tournament():
            payout = balance - self.last_t_balance
            self.last_t_balance = balance
            return payout

        payout = balance - self.last_balance
        self.last_balance = balance
        self.last_t_balance = 0

        return payout

    def get_pots(self) -> (int, int):
        text = self.driver.find_element(By.ID, "odds").text.lower()
        while text == "":
            text = self.driver.find_element(By.ID, "odds").text.lower()
            time.sleep(1)

        amounts = re.findall(r"\$(?:\d|,)+", text)

        if len(amounts) != 2:
            raise RuntimeError(f"Found {len(amounts)} amounts in the pots where we were expecting 2.")

        red_pot, blue_pot = [int(dollars.strip("$").replace(",", "")) for dollars in amounts]

        return red_pot, blue_pot

    def is_tournament(self) -> bool:
        balance = self.driver.find_element(By.ID, "balance")
        return "purple" in balance.get_attribute("class").lower()


if __name__ == '__main__':
    driver = SaltyBetDriver()
    for i in range(1000):
        print(driver.is_tournament())
        time.sleep(1)
