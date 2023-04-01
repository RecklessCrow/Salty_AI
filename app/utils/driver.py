import re
import time

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from utils.settings import settings


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
        time.sleep(settings.SLEEP_TIME)
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
        time.sleep(settings.SLEEP_TIME)
        if "authenticate" in self.driver.current_url.lower():
            raise RuntimeError('Failed to login. Wrong username or password?')

    def __del__(self):
        """
        Close the driver on delete.
        """
        self.driver.close()

    def _get_element_text(self, element_id):
        """
        Retrieves the text of an element by its ID. If the text is invalid, the function blocks until the text is valid.

        Parameters
        ----------
        element_id : str
            ID of the element to parse.

        Returns
        -------
        text : str
            The text contents of the element.

        """
        text = self.driver.find_element(By.ID, element_id).text

        # Got invalid text? Wait until text is valid.
        while not isinstance(text, str) or text == "":
            text = self.driver.find_element(By.ID, element_id).text
            time.sleep(settings.SLEEP_TIME)

        return text

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

        return None

    def get_game_state(self):
        """
        Gets the current state of the game.

        Returns
        -------
        state : int or None
            Enumerated state or None if state could not be decoded.
        """
        encoded_state = self._get_element_text("betstatus").lower()

        if "locked" in encoded_state:
            return settings.STATES["BETS_CLOSED"]

        if "open" in encoded_state:
            return settings.STATES["BETS_OPEN"]

        if "payout" in encoded_state:
            return settings.STATES["PAYOUT"]

        return None

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
        if team not in ["red", "blue"]:
            raise ValueError("Team must be either 'red' or 'blue'")

        if amount <= 0:
            raise ValueError("Amount must be greater than 0")

        time.sleep(settings.SLEEP_TIME)
        wager = self.driver.find_element(By.ID, "wager")
        wager.click()
        wager.clear()
        wager.click()
        wager.send_keys(str(amount))

        time.sleep(settings.SLEEP_TIME)
        self.driver.find_element(By.CLASS_NAME, f"betbutton{team}").click()

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
        red, blue = tuple(odds_text.split(":"))
        return float(red), float(blue)

    def get_fighters(self):
        """
        Gets the names of the red and blue team for the current match.

        Returns
        -------
        (str, str) or None
            Names of the red and blue teams.
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

    def get_current_balance(self):
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
        balance = self.get_current_balance()

        if self.is_tournament():
            payout = balance - self.last_t_balance
            self.last_t_balance = balance
            return payout

        payout = balance - self.last_balance
        self.last_balance = balance
        self.last_t_balance = 0

        return payout

    def get_pots(self):
        text = self._get_element_text("odds")
        amounts = re.findall(r"\$(?:\d|,)+", text)

        if len(amounts) != 2:
            raise RuntimeError(f"Found {len(amounts)} amounts in the pots where we were expecting 2.")

        red_pot, blue_pot = [int(dollars.strip("$").replace(",", "")) for dollars in amounts]

        return red_pot, blue_pot

    def is_tournament(self):
        balance = self.driver.find_element(By.ID, "balance")
        return "purple" in balance.get_attribute("class").lower()


if __name__ == '__main__':
    driver = SaltyBetDriver()
    for i in range(1000):
        print(driver.is_tournament())
        time.sleep(settings.SLEEP_TIME)
