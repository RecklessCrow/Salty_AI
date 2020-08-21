import time

import dotenv
import numpy as np
from selenium import webdriver

from sklearn.preprocessing import LabelEncoder

tier_encoder = LabelEncoder()
tier_encoder.fit(['P', 'B', 'A', 'S', 'X', 'None'])

env = dotenv.DotEnv()
EMAIL = env.get('email')
TOKEN = env.get('password')
driver = webdriver.Chrome('chromedriver.exe')
driver.get("https://www.saltybet.com/authenticate?signin=1")
assert "Salty" in driver.title


def login():
    username = driver.find_element_by_id("email")
    username.clear()
    username.send_keys("jmcc2646@gmail.com")

    password = driver.find_element_by_name("pword")
    password.clear()
    password.send_keys(TOKEN)

    driver.find_element_by_class_name('graybutton').click()


def get_balance():
    balance = int(driver.find_element_by_id('balance').text.replace(',', ''))
    return balance


def get_red_blue():
    red = driver.find_element_by_class_name('betbuttonred').get_attribute('value')
    blue = driver.find_element_by_class_name('betbuttonblue').get_attribute('value')

    return red, blue


def get_bet_status():
    status = driver.find_element_by_id('betstatus').text
    if status == 'Bets are locked until the next match.':
        return None
    if status == 'Bets are OPEN!':
        return None
    if 'Red.' in status.split(' '):
        return "Red"
    if 'Blue.' in status.split(' '):
        return "Blue"

    return None


def get_odds():
    bet_amount, potential_gain, red_odds, blue_odds = driver.find_element_by_id(
        'lastbet').find_elements_by_css_selector('span')
    # todo find more effecient way of formatting
    bet_amount = int(bet_amount.text.replace('$', ''))
    potential_gain = int(potential_gain.text.replace('$', '').replace('+', '').replace('-', ''))
    red_odds = float(red_odds.text)
    blue_odds = float(blue_odds.text)
    return bet_amount, potential_gain, red_odds, blue_odds


def get_stats():
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get('https://www.saltybet.com/stats')

    # wait for page to load
    time.sleep(3)

    red_winrate = driver.find_element_by_id('p1winrate').text.replace('%', '')
    red_matches = driver.find_element_by_id('p1totalmatches').text

    blue_winrate = driver.find_element_by_id('p2winrate').text.replace('%', '')
    blue_matches = driver.find_element_by_id('p2totalmatches').text

    def get_params(player_winrate, player_matches):
        # find out if players are a team
        if '/' in player_winrate:
            winrate = np.array([int(n) for n in player_winrate.split('/')]).mean()
            matches = np.array([int(n) for n in player_matches.split('/')]).mean()
        else:
            winrate = int(player_winrate)
            matches = int(player_matches)

        return winrate, matches

    red_winrate, red_matches = get_params(red_winrate, red_matches)

    blue_winrate, blue_matches = get_params(blue_winrate, blue_matches)

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return np.array([[[red_winrate, red_matches], [blue_winrate, blue_matches]]]).astype('float64')


def get_more_stats():
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get('https://www.saltybet.com/stats')

    # wait for page to load
    time.sleep(3)

    red_winrate = driver.find_element_by_id('p1winrate').text.replace('%', '')
    red_matches = driver.find_element_by_id('p1totalmatches').text
    red_tier = driver.find_element_by_id('p1tier').text
    red_life = driver.find_element_by_id('p1life').text
    red_meter = driver.find_element_by_id('p1meter').text
    red = [red_winrate, red_matches, red_tier, red_life, red_meter]

    blue_winrate = driver.find_element_by_id('p2winrate').text.replace('%', '')
    blue_matches = driver.find_element_by_id('p2totalmatches').text
    blue_tier = driver.find_element_by_id('p2tier').text
    blue_life = driver.find_element_by_id('p2life').text
    blue_meter = driver.find_element_by_id('p2meter').text
    blue = [blue_winrate, blue_matches, blue_tier, blue_life, blue_meter]

    def get_params(stats):
        # find out if players are a team
        if '/' in stats[0]:
            # take avg winrate and matches
            stats[0] = np.array([int(n) for n in stats[0].split('/')]).mean()
            stats[1] = np.array([int(n) for n in stats[1].split('/')]).mean()
            # take highest tier and meter
            stats[2] = np.max([tier_encoder.transform(tier) for tier in stats[2].replace(' ', '').split('/')])
            stats[4] = np.max([tier_encoder.transform(tier) for tier in stats[3].replace(' ', '').split('/')])
            # take sum of health
            stats[3] = np.array([int(n) for n in stats[3].split('/')]).sum()
        else:
            stats[2] = tier_encoder.transform([stats[2]])[0]
            stats = np.array(stats).astype('float64')

        return stats

    red = get_params(red)

    blue = get_params(blue)

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return np.array([[red, blue]]).astype('float64')


def bet(prob, prediction):
    balance = get_balance()

    clip = min(((prob - 0.5) / 0.4), 1)
    modifier = min(np.arcsin(clip) ** 1.25, 1)

    bet_amount = int(np.round(modifier * balance))

    if balance < 3600 * 2 or bet_amount >= balance:
        driver.find_element_by_id('interval10').click()
    else:
        driver.find_element_by_id('wager').send_keys(str(bet_amount))

    # if in tournament bet all in all the time
    # todo find something else this is broken
    # if 'bracket!' in driver.find_element_by_id('footer-alert').text.split(' '):
    #     driver.find_element_by_id('interval10').click()

    # Bet on character
    if prediction == 'Red':
        driver.find_element_by_class_name('betbuttonred').click()
    else:
        driver.find_element_by_class_name('betbuttonblue').click()


def simple_bet(prediction):
    driver.find_element_by_id('wager').send_keys('3600')

    # Bet on character
    if not prediction:
        driver.find_element_by_class_name('betbuttonred').click()
    else:
        driver.find_element_by_class_name('betbuttonblue').click()


if __name__ == '__main__':
    login()
