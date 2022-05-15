from Utils import *
from src.SaltyBetDriver import SaltyBetDriver

"""
Script to gather match data.
Same state machine as Gambler.py but without any betting logic.
"""


def main():
    driver = SaltyBetDriver(headless=True)
    state = STATES["IDLE"]
    start = time.time()

    while True:
        state = await_next_state(driver, state)

        if state == STATES["PAYOUT"]:
            match_time = time.time() - start
            start = time.time()
            record_match(driver, match_time)


if __name__ == '__main__':
    main()
