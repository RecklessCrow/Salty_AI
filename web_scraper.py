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


def get_stats():
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get('https://www.saltybet.com/stats')

    time.sleep(3)

    red_stats = (
        driver.find_element_by_id('p1namestats').text,
        int(driver.find_element_by_id('p1totalmatches').text),
        int(driver.find_element_by_id('p1winrate').text[:-1]),
        int(driver.find_element_by_id('p1life').text),
        int(driver.find_element_by_id('p1meter').text),
        driver.find_element_by_id('p1author').text,
    )

    blue_stats = (
        driver.find_element_by_id('p2namestats').text,
        int(driver.find_element_by_id('p2totalmatches').text),
        int(driver.find_element_by_id('p2winrate').text[:-1]),
        int(driver.find_element_by_id('p2life').text),
        int(driver.find_element_by_id('p2meter').text),
        driver.find_element_by_id('p2author').text,
    )

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return red_stats, blue_stats


def data_collector():
    login()

    last_red = ''
    last_blue = ''

    while True:
        red, blue = get_reb_blue()

        if (red is None or blue is None) or (red == last_red and blue == last_blue):
            continue

        last_red = red
        last_blue = blue

        if 'Team' in red.split(' ') or 'Team' in blue.split(' '):
            time.sleep(1)
            continue

        red_info, blue_info = get_stats()
        database_handler.update_character(red_info)
        database_handler.update_character(blue_info)

        winner = None
        while winner is None:
            winner = get_bet_status()
            time.sleep(1)
            pass

        # print(f'Winner: {winner}\n')
        w = 1
        if winner == 'Red':
            w = 0

        database_handler.add_match(red, blue, w)
        database_handler.connection.commit()

        time.sleep(5)


def bet(probability, prediction):
    probability = probability * 100

    if probability > 80:
        driver.find_element_by_id('interval10').click()
    elif probability > 61:
        driver.find_element_by_id('interval5').click()
    else:
        driver.find_element_by_id('interval1').click()

    if prediction == 'Red':
        driver.find_element_by_class_name('betbuttonred').click()
    else:
        driver.find_element_by_class_name('betbuttonblue').click()


if __name__ == '__main__':
    data_collector()
