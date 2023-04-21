import logging
import threading
import time
from enum import Enum

from utils.driver import driver


class StateMachine:
    class States(Enum):
        START = 0
        BETS_OPEN = 1
        BETS_CLOSED = 2
        PAYOUT = 3

    STATE_UPDATE_INTERVAL = 2  # seconds

    def __init__(self):
        """
        Initializes the state machine.
        """
        self._state = self.States.START
        self._last_state = self.States.START
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def _decode_state_text(self, text: str):
        """
        Decodes the state text from the website.
        """
        if "open" in text:
            return self.States.BETS_OPEN

        if "locked" in text:
            return self.States.BETS_CLOSED

        if "payout" in text:
            return self.States.PAYOUT

        logging.error(f"Unknown state text: {text}")
        raise ValueError

    def update_state(self):
        """
        Updates the state of the state machine.
        """
        while True:
            time.sleep(self.STATE_UPDATE_INTERVAL)
            state_text = driver.get_bet_status()
            state = self._decode_state_text(state_text)
            if state != self._state:
                with self._condition:
                    self._state = state
                    self._condition.notify_all()
                    logging.debug(f"State changed to {state.name}")

    def await_next_state(self):
        """
        Waits for the next state change and returns the new state.
        """
        with self._condition:
            if self._state != self.States.START:
                self._condition.wait_for(lambda: self._state != self._last_state)
            else:
                self._condition.wait_for(lambda: self._state == self.States.BETS_OPEN)
            self._last_state = self._state

        return self._state
