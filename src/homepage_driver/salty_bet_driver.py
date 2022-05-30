import sys

import src.base.base_salty_bet_driver


class SaltyBetDriver(src.base.base_salty_bet_driver.SaltyBetDriver):
    def __init__(self):
        """
        Object to interact with SaltyBet
        :param headless: run web browser in headless mode
        """
        super(SaltyBetDriver, self).__init__(headless=True)

        # login
        self.driver.get("https://www.saltybet.com")

        # Check if successful
        try:
            assert "Salty" in self.driver.title
        except AssertionError:
            print('Failed to load into website. Maybe saltybet.com is down?')
            sys.exit()
