import sys

from selenium.webdriver.common.by import By

import src.base.base_salty_bet_driver


class SaltyBetDriver(src.base.base_salty_bet_driver.SaltyBetDriver):
    def __init__(self, username, password):
        """
        Object to interact with SaltyBet
        :param headless: run web browser in headless mode
        """
        super(SaltyBetDriver, self).__init__(headless=True)

        # Login
        self.driver.get("https://www.saltybet.com/authenticate?signin=1")
        try:
            assert "Salty" in self.driver.title
        except AssertionError:
            print('Failed to load into website. Maybe saltybet.com is down?')
            sys.exit()

        username_element = self.driver.find_element(By.ID, "email")
        username_element.clear()
        username_element.send_keys(username)

        password_element = self.driver.find_element(By.NAME, "pword")
        password_element.clear()
        password_element.send_keys(password)

        self.driver.find_element(By.CLASS_NAME, 'graybutton').click()
