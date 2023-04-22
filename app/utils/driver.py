import logging
import re
import time
from math import floor

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, \
    NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.utils.settings import settings


class SaltyBetDriver:
    VALID_TEAMS = {"red", "blue"}

    def __init__(self):
        """
        Initialize the driver.

        This will load the website and login.

        Raises
        ------
        RuntimeError
            If the driver fails to load the website.
            If the driver fails to log in.
        """
        print("Initializing driver")
        self.last_balance = 0
        self.last_balance_tournament = 0

        self.winnings = 0
        self.winnings_tournament = 0

        options = Options()
        options.add_argument("--headless")

        self.driver = webdriver.Firefox(options=options)
        self.wait = WebDriverWait(self.driver, settings.WAIT_TIME)

        # Load into the website
        self.driver.get("https://www.saltybet.com/authenticate?signin=1")
        try:
            self.wait.until(EC.title_contains("Salty Bet"))
        except TimeoutException:
            logging.error("Failed to load into website. Maybe saltybet.com is down?")
            raise RuntimeError

        # Login
        username_element = self.driver.find_element(By.ID, "email")
        username_element.clear()
        username_element.send_keys(settings.SALTYBET_USERNAME)

        password_element = self.driver.find_element(By.NAME, "pword")
        password_element.clear()
        password_element.send_keys(settings.SALTYBET_PASSWORD)

        self.driver.find_element(By.CLASS_NAME, 'graybutton').click()

        try:
            self.wait.until_not(EC.url_contains("authenticate"))
        except TimeoutException:
            logging.error("Failed to login. Wrong username or password?")
            raise RuntimeError

        print("Driver initialized")

    def __del__(self):
        """
        Close the driver on delete.

        This will close the browser window.
        """
        print("Closing driver")
        try:
            self.driver.quit()
        except WebDriverException:
            pass
        print("Driver closed")

    def _get_element_text(self, element_id):
        """
        Retrieves the text of an element by its ID. If the text is invalid, the function blocks until the text is valid.

        Parameters
        ----------
        element_id : str
            ID of the element to parse.

        Returns
        -------
        text : str or None
            The text contents of the element. None if the element does not exist or cannot be found.

        Notes
        -----
        The text is invalid if it is empty or contains only whitespace.
        This function blocks until the text is valid.
        """
        try:
            element = self.wait.until(EC.presence_of_element_located((By.ID, element_id)))
            text = self.wait.until(lambda _: element.text.strip())
            return text

        except (NoSuchElementException, TimeoutException):
            return None

    def get_winner(self):
        """
        Gets the winning team of the last match, either "red" or "blue".

        Returns
        -------
        winner : str or None
            The winning team. None if there was a tie.
        """

        payout_message = self._get_element_text("betstatus").lower()

        if "red" in payout_message:
            return "red"

        if "blue" in payout_message:
            return "blue"

        return None  # Tie or unknown

    def get_bet_status(self):
        """
        Gets the current state of the game.

        Returns
        -------
        state : str
            The current state of the game.
        """
        return self._get_element_text("betstatus").lower()

    def place_bet(self, amount, team):
        """
        Places a bet on a SaltyBet match.

        Parameters
        ----------
        amount : int
            Amount to bet.
        team : str
            Team to bet on. Must be one of ``['red', 'blue']``.
        """

        if team not in self.VALID_TEAMS:
            raise ValueError(f'Team must be one of {self.VALID_TEAMS}')

        if amount <= 0:
            raise ValueError('Amount must be greater than 0')

        if not isinstance(amount, int):
            amount = floor(amount)

        wager = self.driver.find_element(By.ID, 'wager')
        wager.clear()
        wager.send_keys(str(amount))

        button_class = f'betbutton{team}'
        bet_button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, button_class))
        )
        bet_button.click()

    def get_odds(self):
        """
        Get the odds of the current match.

        Returns
        -------
        (float, float)
            Betting odds of the current match.
        """
        betting_text = self._get_element_text("lastbet")

        odds_text = betting_text.split("|")[-1].strip()
        red, blue = tuple(map(float, odds_text.split(":")))
        return red, blue

    def get_match_up(self):
        """
        Gets the names of the red and blue team for the current match.

        Returns
        -------
        (str, str) or None
            Names of the red and blue teams.
        """
        red_elements = self.driver.find_elements(By.CLASS_NAME, "redtext")
        blue_elements = self.driver.find_elements(By.CLASS_NAME, "bluetext")

        if len(red_elements) > 0 and len(blue_elements) > 0:
            red = red_elements[0].text
            blue = blue_elements[0].text

            if "|" in red:  # Number of betters is in the text. Example blue = "Cci hinako | 56"
                red = red.split('|')[1]
                blue = blue.split('|')[0]

            return red.strip(), blue.strip()

        return None, None

    def get_balance(self):
        """
        Gets the current balance for the logged in account.

        Returns
        -------
        balance : int
            Current balance.
        """
        balance_text = self._get_element_text("balance")

        balance = int(balance_text.replace(",", ""))

        if self.last_balance == 0:
            self.last_balance = balance

        return balance

    def get_payout(self):
        """
        Gets the payout for the current match.

        Returns
        -------
        payout : int
            The payout for the last match.
        """
        balance = self.get_balance()

        if self.is_tournament():
            payout = balance - self.last_balance_tournament
            self.last_balance_tournament = balance
            return payout

        payout = balance - self.last_balance
        self.last_balance = balance
        self.last_balance_tournament = 0

        return payout

    def get_pots(self):
        """
        Gets the amounts of the red and blue pots for the current match.

        Returns
        -------
        (int, int)
            Amounts of the red and blue pots.
        """
        text = self._get_element_text("odds")

        amounts = re.findall(r"\$(\d[\d,]*)", text)

        if len(amounts) != 2:
            raise RuntimeError(f"Could not parse pots from text: {text}")

        red_pot, blue_pot = [int(amount.replace(",", "")) for amount in amounts]

        return red_pot, blue_pot

    def is_tournament(self):
        balance = self.driver.find_element(By.ID, "balance")
        return "purple" in balance.get_attribute("class").lower()


driver = SaltyBetDriver()

if __name__ == '__main__':
    for i in range(1000):
        print(driver.is_tournament())
        time.sleep(settings.SLEEP_TIME)
