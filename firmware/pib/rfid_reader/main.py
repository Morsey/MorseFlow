from machine import Pin
from neopixel import NeoPixel
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms
import ujson
import uos

import config
from pn5180_morse import NFC


STATE_NO_CARD = "no_card"
STATE_CORRECT = "correct"
STATE_WRONG = "wrong"
STATE_ERROR = "error"

COLOR_OFF = (0, 0, 0)
COLOR_NO_CARD = (2, 2, 2)
COLOR_CORRECT = (0, 4, 0)
COLOR_WRONG = (4, 0, 0)
COLOR_ERROR = (4, 0, 0)


def log(message):
    if config.DEBUG_REPL:
        print(message)


def uid_to_hex(uid):
    if not uid:
        return None
    return "".join("{:02X}".format(value) for value in uid)


def valid_uid_hex(card_id):
    if not card_id:
        return False
    if "FFFFFFFF" in card_id:
        return False
    if config.CARD_TYPE == "ISO14443":
        return len(card_id) in (8, 14, 20)
    if config.CARD_TYPE == "ISO15693":
        return len(card_id) == 16
    return len(card_id) >= 8 and len(card_id) <= 20 and len(card_id) % 2 == 0


def load_correct_cards():
    try:
        with open(config.CARD_STORE_PATH, "r") as handle:
            data = ujson.load(handle)
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {uid: "stored" for uid in data}
    except OSError:
        return dict(config.DEFAULT_CORRECT_CARD_IDS)
    except Exception as exc:
        print("Card store load failed:", exc)
    return {}


def save_correct_cards(cards):
    path = config.CARD_STORE_PATH
    temp_path = path + ".tmp"
    with open(temp_path, "w") as handle:
        ujson.dump(cards, handle)
    try:
        uos.remove(path)
    except OSError:
        pass
    uos.rename(temp_path, path)


class Button:
    def __init__(self, pin_number):
        self.pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
        self.stable_pressed = self._raw_pressed()
        self.last_raw_pressed = self.stable_pressed
        self.last_change_ms = ticks_ms()

    def _raw_pressed(self):
        value = self.pin.value()
        if config.BUTTON_ACTIVE_LOW:
            return value == 0
        return value == 1

    def update(self, now_ms):
        raw_pressed = self._raw_pressed()
        changed = False

        if raw_pressed != self.last_raw_pressed:
            self.last_raw_pressed = raw_pressed
            self.last_change_ms = now_ms

        if (
            raw_pressed != self.stable_pressed
            and ticks_diff(now_ms, self.last_change_ms) >= config.BUTTON_DEBOUNCE_MS
        ):
            self.stable_pressed = raw_pressed
            changed = True

        return changed

    def pressed(self):
        return self.stable_pressed


class CardButtons:
    def __init__(self):
        self.add = Button(config.ADD_BUTTON_PIN)
        self.remove = Button(config.REMOVE_BUTTON_PIN)
        self.last_combo_pressed = self.add.pressed() and self.remove.pressed()

    def update(self, now_ms):
        add_changed = self.add.update(now_ms)
        remove_changed = self.remove.update(now_ms)
        add_pressed = self.add.pressed()
        remove_pressed = self.remove.pressed()
        combo_pressed = add_pressed and remove_pressed

        if combo_pressed and not self.last_combo_pressed:
            self.last_combo_pressed = True
            return "clear"
        if not combo_pressed:
            self.last_combo_pressed = False

        if add_changed and add_pressed and not remove_pressed:
            return "add"
        if remove_changed and remove_pressed and not add_pressed:
            return "remove"
        return None


class StatusOutputs:
    def __init__(self):
        self.correct = Pin(config.STATUS_CORRECT_PIN, Pin.OUT)
        self.wrong = Pin(config.STATUS_WRONG_PIN, Pin.OUT)
        self.set_state(STATE_NO_CARD)

    def set_state(self, state):
        self.correct.value(1 if state == STATE_CORRECT else 0)
        self.wrong.value(1 if state == STATE_WRONG else 0)


class StatusPixel:
    def __init__(self):
        self.pixels = None
        try:
            self.pixels = NeoPixel(Pin(config.NEOPIXEL_PIN, Pin.OUT), config.NEOPIXEL_COUNT)
        except Exception as exc:
            print("NeoPixel unavailable:", exc)

    def set(self, color):
        if not self.pixels:
            return
        for index in range(config.NEOPIXEL_COUNT):
            self.pixels[index] = color
        self.pixels.write()


class RFIDReaderPIB:
    def __init__(self):
        self.outputs = StatusOutputs()
        self.pixel = StatusPixel()
        self.buttons = CardButtons()
        self.correct_cards = load_correct_cards()
        self.reader = None
        self.state = None
        self.card_id = None
        self.pending_card_id = None
        self.pending_card_reads = 0
        self.pending_card_last_seen_ms = 0
        self.miss_count = 0
        self.next_poll_ms = 0
        self.next_init_ms = 0
        self.next_status_log_ms = 0

        log("RFID PIB booting")
        log("Known correct cards: {}".format(len(self.correct_cards)))
        self._set_state(STATE_NO_CARD, None)
        self._init_reader()

    def update(self, now_ms):
        action = self.buttons.update(now_ms)
        if action:
            self._handle_button_action(action)

        if self.reader is None:
            if ticks_diff(now_ms, self.next_init_ms) >= 0:
                self._init_reader()
            return

        if ticks_diff(now_ms, self.next_status_log_ms) >= 0:
            self.next_status_log_ms = ticks_add(now_ms, config.STATUS_LOG_INTERVAL_MS)
            log(
                "Status: state={} card={} known={}".format(
                    self.state,
                    self.card_id,
                    len(self.correct_cards),
                )
            )

        if ticks_diff(now_ms, self.next_poll_ms) < 0:
            return
        self.next_poll_ms = ticks_add(now_ms, config.POLL_INTERVAL_MS)

        try:
            raw_card_id = self.read_card_id()
        except Exception as exc:
            print("RFID scan failed:", exc)
            self.reader = None
            self.next_init_ms = ticks_add(now_ms, config.SCAN_ERROR_BACKOFF_MS)
            self._set_state(STATE_ERROR, None)
            return

        card_id = self._stable_card_id(raw_card_id, now_ms)

        if card_id:
            self.miss_count = 0
            if card_id in self.correct_cards:
                self._set_state(STATE_CORRECT, card_id)
            else:
                self._set_state(STATE_WRONG, card_id)
            return

        self.miss_count += 1
        if self.miss_count >= config.MISS_THRESHOLD:
            self._set_state(STATE_NO_CARD, None)

    def read_card_id(self):
        uid = self.reader.read_card_serial(config.CARD_TYPE)
        return uid_to_hex(uid)

    def _stable_card_id(self, raw_card_id, now_ms):
        if raw_card_id and not valid_uid_hex(raw_card_id):
            log("Ignored invalid UID: {}".format(raw_card_id))
            raw_card_id = None

        if not raw_card_id:
            if (
                self.pending_card_id
                and ticks_diff(now_ms, self.pending_card_last_seen_ms)
                > config.CARD_STABLE_WINDOW_MS
            ):
                self.pending_card_id = None
                self.pending_card_reads = 0
            return None

        if raw_card_id == self.card_id:
            self.pending_card_id = raw_card_id
            self.pending_card_reads = config.CARD_STABLE_READS
            self.pending_card_last_seen_ms = now_ms
            return raw_card_id

        if raw_card_id == self.pending_card_id:
            self.pending_card_reads += 1
        else:
            self.pending_card_id = raw_card_id
            self.pending_card_reads = 1
        self.pending_card_last_seen_ms = now_ms

        if self.pending_card_reads < config.CARD_STABLE_READS:
            log(
                "Pending UID {} ({}/{})".format(
                    raw_card_id,
                    self.pending_card_reads,
                    config.CARD_STABLE_READS,
                )
            )
            return None

        return raw_card_id

    def _init_reader(self):
        try:
            log("Initializing PN5180 reader...")
            self.reader = NFC(
                config.PN5180_NSS_PIN,
                config.PN5180_RST_PIN,
                config.PN5180_BSY_PIN,
                card_reader_id="pib-rfid",
                sck=config.PN5180_SCK_PIN,
                mosi=config.PN5180_MOSI_PIN,
                miso=config.PN5180_MISO_PIN,
            )
            self.reader.begin()
            sleep_ms(50)
            if not self.reader.reset():
                raise ValueError("PN5180 reset failed")

            firmware = self.reader.get_firmware()
            product = self.reader.get_product_version()
            eeprom = self.reader.get_eeprom_version()
            log("PN5180 firmware: {}".format(firmware))
            log("PN5180 product: {}".format(product))
            log("PN5180 EEPROM: {}".format(eeprom))
            log("PN5180 ready, card type {}".format(config.CARD_TYPE))
            self._set_state(STATE_NO_CARD, None)
        except Exception as exc:
            print("PN5180 init failed:", exc)
            self.reader = None
            self.next_init_ms = ticks_add(ticks_ms(), config.SCAN_ERROR_BACKOFF_MS)
            self._set_state(STATE_ERROR, None)

    def _handle_button_action(self, action):
        if action == "clear":
            self.correct_cards = {}
            save_correct_cards(self.correct_cards)
            print("Correct card list cleared")
            self._refresh_current_card_state()
            return

        if not self.card_id:
            print("Button {} ignored: no card present".format(action))
            return

        if action == "add":
            self.correct_cards[self.card_id] = "learned"
            save_correct_cards(self.correct_cards)
            print("Card added:", self.card_id)
        elif action == "remove":
            if self.card_id in self.correct_cards:
                del self.correct_cards[self.card_id]
                save_correct_cards(self.correct_cards)
                print("Card removed:", self.card_id)
            else:
                print("Card not in correct list:", self.card_id)

        self._refresh_current_card_state()

    def _refresh_current_card_state(self):
        if not self.card_id:
            self._set_state(STATE_NO_CARD, None)
        elif self.card_id in self.correct_cards:
            self._set_state(STATE_CORRECT, self.card_id)
        else:
            self._set_state(STATE_WRONG, self.card_id)

    def _set_state(self, state, card_id):
        if state == self.state and card_id == self.card_id:
            return

        self.state = state
        self.card_id = card_id
        self.outputs.set_state(state)
        log("State: {} card={}".format(state, card_id))

        if state == STATE_CORRECT:
            self.pixel.set(COLOR_CORRECT)
        elif state == STATE_WRONG:
            self.pixel.set(COLOR_WRONG)
        elif state == STATE_ERROR:
            self.pixel.set(COLOR_ERROR)
        else:
            self.pixel.set(COLOR_NO_CARD)

        if config.SERIAL_REPORT_CARD_ID:
            print({
                "state": state,
                "card_id": card_id,
                "known_cards": len(self.correct_cards),
            })


def main():
    pib = RFIDReaderPIB()
    while True:
        pib.update(ticks_ms())
        sleep_ms(5)


main()
