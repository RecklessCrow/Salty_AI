import sys
import time

import dotenv
import numpy as np
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from sklearn.preprocessing import OneHotEncoder

te = OneHotEncoder()
te.fit(np.array(['P', 'B', 'A', 'S', 'X']).reshape(-1, 1))


class WebScraper:

    def __init__(self):
        self.driver = webdriver.Chrome('chromedriver.exe')
        self.login()

    @property
    def balance(self):
        return int(self.driver.find_element_by_id('balance').text.replace(',', ''))

    @property
    def status(self):
        return self.driver.find_element_by_id('betstatus').text.lower()

    def login(self):

        self.driver.get("https://www.saltybet.com/authenticate?signin=1")
        try:
            assert "Salty" in self.driver.title
        except AssertionError:
            print('Failed to load into website. (maybe saltybet.com is down?)')
            sys.exit()

        env = dotenv.DotEnv()
        EMAIL = env.get('email')
        TOKEN = env.get('password')

        username = self.driver.find_element_by_id("email")
        username.clear()
        username.send_keys(EMAIL)

        password = self.driver.find_element_by_name("pword")
        password.clear()
        password.send_keys(TOKEN)

        self.driver.find_element_by_class_name('graybutton').click()

    def get_player_names(self):
        red = self.driver.find_element_by_id('sbettors1').find_element_by_class_name('redtext').text
        blue = self.driver.find_element_by_id('sbettors2').find_element_by_class_name('bluetext').text

        if '|' in red:
            red = red.replace(' ', '').split('|')[1]

        if '|' in blue:
            blue = blue.replace(' ', '').split('|')[0]

        return red, blue

    def get_odds(self):
        info = ()

        # todo add time out for when the bot didnt place bet in time
        # todo Sometimes driver returns a tuple with less than 4 elements. Find more elegant way of doing this
        while len(info) != 4:
            try:
                info = self.driver.find_element_by_id('lastbet').find_elements_by_css_selector('span')
            except StaleElementReferenceException:
                pass
            time.sleep(5)

        bet_amount, potential_gain, red_odds, blue_odds = info

        if "" in info:
            return self.get_odds()

        # cast strings to numbers
        bet_amount = int(bet_amount.text[1:])
        potential_gain = int(potential_gain.text[2:])
        red_odds = float(red_odds.text)
        blue_odds = float(blue_odds.text)
        return bet_amount, potential_gain, red_odds, blue_odds

    @staticmethod
    def _format_team(team_stats):
        win_rate, num_matches, life, meter, tier = [stat.replace(' ', '').split('/') for stat in team_stats]
        # take avg winrate and num_matches
        win_rate = np.array(list(map(int, win_rate))).mean()
        num_matches = np.array(list(map(int, num_matches))).mean()
        # take sum live
        life = sum(list(map(int, life)))
        # take max meter and tier
        meter = max(list(map(int, meter)))

        if None in tier:
            tier = np.zeros(5)
        else:
            a = te.transform(tier[0]).toarray()[0]
            b = te.transform(tier[1]).toarray()[0]
            if np.argmax(a) > np.argmax(b):
                tier = a
            else:
                tier = b

        return [win_rate, num_matches, life, meter] + tier

    def get_stats(self):
        formatted_stats = []
        for p in [1, 2]:
            stats = self.driver.find_element_by_id(f'bettors{p}')
            bettor_lines = stats.find_elements_by_class_name('bettor-line')
            goldtext = stats.find_elements_by_css_selector('span')
            stats = [x.text[len(i.text):] for x, i in zip(bettor_lines, goldtext)][:-2]
            num_matches, win_rate, tier, life, meter = stats
            stats[1] = win_rate.replace('%', '')

            if '/' in num_matches:
                formatted_stats.append(self._format_team(stats))
                continue

            win_rate = int(win_rate.replace('%', ''))
            num_matches = int(num_matches)
            life = int(life)
            meter = int(meter)
            tier = te.transform([[tier.replace(' ', '')]]).toarray()[0]

            stats = [win_rate, num_matches, life, meter] + list(tier)
            formatted_stats.append(stats)

        return np.array(formatted_stats).reshape((1, 2, 9))

    def bet(self, amount, team):
        self.driver.find_element_by_id('wager').send_keys(str(amount))
        self.driver.find_element_by_class_name(f'betbutton{team}').click()

    def close(self):
        self.driver.close()


if __name__ == '__main__':
    ws = WebScraper()
    while True:
        print(ws.get_odds())
