import time

import dotenv
from selenium import webdriver

import database_handler

env = dotenv.DotEnv()
EMAIL = env.get('email')
TOKEN = env.get('password')
driver = webdriver.Chrome('chromedriver.exe')


def login(a_driver=driver):
    a_driver.get("https://www.saltybet.com/authenticate?signin=1")
    assert "Salty" in driver.title
    username = a_driver.find_element_by_id("email")
    username.clear()
    username.send_keys("jmcc2646@gmail.com")

    password = a_driver.find_element_by_name("pword")
    password.clear()
    password.send_keys(TOKEN)

    a_driver.find_element_by_class_name('graybutton').click()


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
    temp_driver = webdriver.Chrome('chromedriver.exe')
    login(temp_driver)
    temp_driver.get('https://www.saltybet.com/stats')

    time.sleep(2)

    red_stats = {
        'name': temp_driver.find_element_by_id('p1namestats').text,
        'num_matches': temp_driver.find_element_by_id('p1totalmatches').text,
        'win_rate': temp_driver.find_element_by_id('p1winrate').text,
        'life': temp_driver.find_element_by_id('p1life').text,
        'meter': temp_driver.find_element_by_id('p1meter').text,
        'author': temp_driver.find_element_by_id('p1author').text,
    }

    blue_stats = {
        'name': temp_driver.find_element_by_id('p2namestats').text,
        'num_matches': temp_driver.find_element_by_id('p2totalmatches').text,
        'win_rate': temp_driver.find_element_by_id('p2winrate').text,
        'life': temp_driver.find_element_by_id('p2life').text,
        'meter': temp_driver.find_element_by_id('p2meter').text,
        'author': temp_driver.find_element_by_id('p2author').text,
    }

    temp_driver.close()

    return red_stats, blue_stats


def data_collector():
    login()

    while True:
        red, blue = get_reb_blue()

        if 'Team' in red.split(' ') or 'Team' in blue.split(' '):
            time.sleep(1)
            continue

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

        return red, blue, w


def bet(probability, prediction):
    probability = probability * 100

    if probability > 75:
        driver.find_element_by_id('interval10').click()
    elif probability > 65:
        driver.find_element_by_id('interval5').click()
    else:
        driver.find_element_by_id('interval1').click()

    if prediction == 'Red':
        driver.find_element_by_class_name('betbuttonred').click()
    else:
        driver.find_element_by_class_name('betbuttonblue').click()


if __name__ == '__main__':
    login()
    get_stats()
    driver.close()
