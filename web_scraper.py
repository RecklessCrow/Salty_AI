import time

import dotenv
import numpy as np
from selenium import webdriver

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
    balance = int(driver.find_element_by_id('balance').text)
    return balance


def get_reb_blue():
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


def get_stats():
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get('https://www.saltybet.com/stats')

    time.sleep(3)

    red_winrate = driver.find_element_by_id('p1winrate').text,
    red_matches = driver.find_element_by_id('p1totalmatches').text

    blue_winrate = driver.find_element_by_id('p2winrate').text,
    blue_matches = driver.find_element_by_id('p2totalmatches').text

    # find out if players are a team
    if '/' in red_winrate:
        red_winrate = np.array([int(n) for n in red_winrate.split('/')]).mean()
        red_matches = np.array([int(n) for n in red_matches.split('/')]).mean()

    else:
        red_winrate = int(red_winrate[0][:-1])
        red_matches = int(red_matches)

    if '/' in blue_winrate:
        blue_winrate = np.array([int(n[:-1]) for n in blue_winrate.split('/')]).mean()[0]
        blue_matches = np.array([int(n[:-1]) for n in blue_matches.split('/')]).mean()[0]
    else:
        blue_winrate = int(blue_winrate[0][:-1])
        blue_matches = int(blue_matches)

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return np.array([[[red_winrate, red_matches], [blue_winrate, blue_matches]]]).astype('float64')


def bet(probability, prediction):
    if probability < 0.55:
        driver.find_element_by_id('wager').send_keys('1')

    modifier = (probability - 0.55) / 0.25
    bet_amount = modifier * get_balance()
    driver.find_element_by_id('wager').send_keys(bet_amount)

    # if in tournament bet all in all the time
    # todo find something else this is broken
    if 'bracket!' in driver.find_element_by_id('footer-alert').text.split(' '):
        driver.find_element_by_id('interval10').click()

    # Bet on character
    if prediction == 'Red':
        driver.find_element_by_class_name('betbuttonred').click()
    else:
        driver.find_element_by_class_name('betbuttonblue').click()


if __name__ == '__main__':
    login()
    print(get_stats())
    driver.close()
    pass
