from machine import Pin
from time import ticks_add, ticks_diff, ticks_ms

import config


STATE_NO_CARD = "no_card"
STATE_CORRECT = "correct"
STATE_INCORRECT = "incorrect"


class RFIDReaderPIB:
    def __init__(self):
        self.correct_out = Pin(config.STATUS_CORRECT_PIN, Pin.OUT)
        self.incorrect_out = Pin(config.STATUS_INCORRECT_PIN, Pin.OUT)
        self.next_poll_ms = 0
        self.state = None
        self.card_id = None
        self._set_state(STATE_NO_CARD, None)

    def update(self, now_ms):
        if ticks_diff(now_ms, self.next_poll_ms) < 0:
            return
        self.next_poll_ms = ticks_add(now_ms, config.POLL_INTERVAL_MS)

        card_id = self.read_card_id()
        if card_id is None:
            self._set_state(STATE_NO_CARD, None)
        elif card_id in config.CORRECT_CARD_IDS:
            self._set_state(STATE_CORRECT, card_id)
        else:
            self._set_state(STATE_INCORRECT, card_id)

    def read_card_id(self):
        # Integrate a PN5180 MicroPython driver here.
        return None

    def _set_state(self, state, card_id):
        if state == self.state and card_id == self.card_id:
            return

        self.state = state
        self.card_id = card_id

        self.correct_out.value(1 if state == STATE_CORRECT else 0)
        self.incorrect_out.value(1 if state == STATE_INCORRECT else 0)

        if config.SERIAL_REPORT_CARD_ID:
            print({
                "state": state,
                "card_id": card_id,
            })


def main():
    pib = RFIDReaderPIB()
    while True:
        pib.update(ticks_ms())


main()

