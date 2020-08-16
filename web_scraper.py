import os
from time import sleep
from dotenv import load_dotenv
from selenium import webdriver

load_dotenv()
EMAIL = os.getenv('email')
TOKEN = os.getenv('password')
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

    return status


if __name__ == '__main__':
    login()
    previous_red = ''
    previous_blue = ''
    while True:
        red, blue = get_reb_blue()
        if previous_red != red or previous_blue != blue:
            previous_red = red
            previous_blue = blue
            print(f'{red} vs. {blue}')
        sleep(10)
