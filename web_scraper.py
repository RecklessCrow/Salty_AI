import time

import dotenv
from selenium import webdriver

import database_handler

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
    balance = driver.find_element_by_id('balance').text
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


def data_collector():
    login()

    while True:
        red, blue = get_reb_blue()

        if 'Team' in red.split(' ') or 'Team' in blue.split(' '):
            time.sleep(1)
            continue

        print(f'Red: {red}\n'
              f'Blue: {blue}\n')

        winner = None
        while winner is None:
            winner = get_bet_status()
            time.sleep(1)
            pass

        print(f'Winner: {winner}\n')

        w = 1
        if winner == 'Red':
            w = 0

        database_handler.add_match(red, blue, w)
        database_handler.connection.commit()

        time.sleep(5)

        return red, blue, w


if __name__ == '__main__':
    data_collector()
