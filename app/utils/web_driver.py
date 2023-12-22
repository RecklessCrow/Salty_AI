import logging
import re
import time

from math import floor
from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.config import config


class WebDriver:
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
        self.logger = logging.getLogger("WebDriver")
        self.logger.info("Initializing driver")

        self.sleep_time = 0.5

        self.last_balance = 0
        self.last_balance_tournament = 0

        self.winnings = 0
        self.winnings_tournament = 0

        options = Options()
        options.add_argument("--headless")

        self.driver = webdriver.Firefox(options=options)
        self.wait = WebDriverWait(self.driver, config.WAIT_TIME)

        # Load into the website
        self.driver.get("https://www.saltybet.com/authenticate?signin=1")
        try:
            self.wait.until(EC.title_contains("Salty Bet"))
        except TimeoutException:
            logging.error("Failed to load into website. Maybe saltybet.com is down?")
            raise RuntimeError

        # Login
        username_element = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        username_element.clear()
        username_element.send_keys(config.SALTYBET_USERNAME)

        password_element = self.wait.until(EC.presence_of_element_located((By.ID, "pword")))
        password_element.clear()
        password_element.send_keys(config.SALTYBET_PASSWORD)

        self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "graybutton"))).click()

        try:
            self.wait.until_not(EC.url_contains("authenticate"))
        except TimeoutException:
            logging.error("Failed to login. Wrong username or password?")
            raise RuntimeError

        logging.info("Driver initialized")

    def __del__(self):
        """
        Close the driver on delete.

        This will close the browser window.
        """
        self.logger.info("Closing driver")
        try:
            self.driver.quit()
        except WebDriverException:
            logging.warning("Failed to call driver.quit()")

        logging.info("Driver closed")

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
        # self.logger.info(f"Getting element text for {element_id}")
        try:
            element = self.wait.until(EC.presence_of_element_located((By.ID, element_id)))
            text = ""

            while not text.strip():
                text = element.text
                time.sleep(self.sleep_time)

            return text.strip()

        except NoSuchElementException:
            self.logger.warning(f"Failed to get element text for {element_id}")
            return None
        except TimeoutException:
            self.logger.warning(f"Timeout while waiting for element {element_id} to load")
            return None

    def get_winner(self):
        """
        Gets the winning team of the last match, either "red" or "blue".

        Returns
        -------
        winner : str or None
            The winning team. None if there was a tie.
        """
        self.logger.info("Getting winner")
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
        self.logger.info("Getting bet status")
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
        self.logger.info(f"Placing bet of {amount} on {team}")

        if team not in self.VALID_TEAMS:
            raise ValueError(f'Team must be one of {self.VALID_TEAMS}')

        if amount <= 0:
            raise ValueError('Amount must be greater than 0')

        if not isinstance(amount, int):
            amount = floor(amount)

        wager = self.wait.until(EC.element_to_be_clickable((By.ID, "wager")))
        wager.clear()
        wager.send_keys(str(amount))

        button_class = f'betbutton{team}'
        bet_button = self.wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, button_class))
        )
        bet_button.click()

    def place_bet_with_retry(self, wager, bet_on, num_retries=3):
        """
        Places a bet on a SaltyBet match.
        """
        for idx in range(num_retries):
            try:
                self.place_bet(wager, bet_on)
                return  True  # Indicate success
            except TimeoutException as e:
                if idx == num_retries - 1:
                    self.logger.error(f"Failed to place bet: {e}")
                    return False  # Indicate failure

    def get_odds(self):
        """
        Get the odds of the current match.

        Returns
        -------
        (float, float)
            Betting odds of the current match.
        """
        self.logger.info("Getting odds")
        betting_text = self._get_element_text("lastbet")

        # Find all numbers inbetween the ":" i.e. the odds
        odds = re.findall(r"(?<!\$)\b\d+(?:\.\d+)?\b(?![^:]*\d)", betting_text)

        if len(odds) != 2:
            logging.warning(f"Failed to parse odds from {betting_text}")
            return 0.0, 0.0

        red, blue = [float(x) for x in odds]
        return red, blue

    def get_match_up(self):
        """
        Gets the names of the red and blue team for the current match.

        Returns
        -------
        (str, str) or None
            Names of the red and blue teams.
        """
        self.logger.info("Getting match up")
        try:
            red_element = self.wait.until(EC.presence_of_element_located((By.ID, "sbettors1")))
            red_element = red_element.find_element(By.CLASS_NAME, "redtext")
            blue_element = self.wait.until(EC.presence_of_element_located((By.ID, "sbettors2")))
            blue_element = blue_element.find_element(By.CLASS_NAME, "bluetext")
            red = ''
            blue = ''

            while not red.strip() or not blue.strip():
                red = red_element.text
                blue = blue_element.text

                if "|" in red or "|" in blue:
                    red = red.split("|")[1].strip()
                    blue = blue.split("|")[0].strip()

                time.sleep(self.sleep_time)

            return red, blue

        except NoSuchElementException:
            self.logger.warning("Failed to get match up")
            return None
        except TimeoutException:
            self.logger.warning("Timeout while waiting for match up to load")
            return None

    def get_balance(self):
        """
        Gets the current balance for the logged in account.

        Returns
        -------
        balance : int
            Current balance.
        """
        self.logger.info("Getting balance")
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
        self.logger.info("Getting payout")
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
        self.logger.info("Getting pots")
        text = self._get_element_text("odds")

        amounts = re.findall(r"\$(\d[\d,]*)", text)

        if len(amounts) != 2:
            logging.warning(f"Could not parse pots from text: {text}")
            return 0, 0

        red_pot, blue_pot = [int(amount.replace(",", "")) for amount in amounts]

        return red_pot, blue_pot

    def is_tournament(self):
        self.logger.info("Checking if tournament")
        balance = self.wait.until(EC.presence_of_element_located((By.ID, "balance")))
        return "purple" in balance.get_attribute("class").lower()


driver = WebDriver()

if __name__ == '__main__':
    for i in range(1000):
        print(driver.get_match_up())
        time.sleep(1)
