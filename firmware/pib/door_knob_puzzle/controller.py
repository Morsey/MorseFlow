from machine import Pin
from time import ticks_add, ticks_diff

import config
from debug import log


class DoorKnobController:
    ROW_COUNT = 4
    COLUMN_COUNT = 5
    BOOK_COUNT = 10

    def __init__(self):
        self.configured = self._pins_configured()
        self.rows = []
        self.columns = []
        self.raw_switches = [[False] * self.COLUMN_COUNT for _ in range(self.ROW_COUNT)]
        self.switches = [[False] * self.COLUMN_COUNT for _ in range(self.ROW_COUNT)]
        self.candidate_switches = [[False] * self.COLUMN_COUNT for _ in range(self.ROW_COUNT)]
        self.candidate_counts = [[0] * self.COLUMN_COUNT for _ in range(self.ROW_COUNT)]
        self.book_states = ["unknown"] * self.BOOK_COUNT
        self.next_scan_ms = 0
        self.scan_count = 0
        self.events = []
        self.last_error = None

        if not self.configured:
            self.last_error = "book matrix GPIO pins are not configured"
            log("controller", self.last_error)
            return

        self.columns = [self._make_column(pin) for pin in config.BOOK_COLUMN_PINS]
        self.rows = [Pin(pin, Pin.IN) for pin in config.BOOK_ROW_PINS]
        log("controller", "book matrix initialized: 4 rows x 5 columns")

    def _pins_configured(self):
        row_pins = tuple(config.BOOK_ROW_PINS)
        column_pins = tuple(config.BOOK_COLUMN_PINS)
        pins = row_pins + column_pins
        return (
            len(row_pins) == self.ROW_COUNT
            and len(column_pins) == self.COLUMN_COUNT
            and len(set(pins)) == len(pins)
        )

    def update(self, now_ms):
        if not self.configured or ticks_diff(now_ms, self.next_scan_ms) < 0:
            return False
        self.next_scan_ms = ticks_add(now_ms, config.BOOK_SCAN_INTERVAL_MS)
        try:
            readings = self._scan_matrix()
            self.last_error = None
        except Exception as exc:
            error = repr(exc)
            if error != self.last_error:
                self.last_error = error
                self.events.append(("error", {"source": "book_matrix", "error": error}))
                return True
            return False

        self.scan_count += 1
        changed_books = set()
        for row in range(self.ROW_COUNT):
            for column in range(self.COLUMN_COUNT):
                raw = readings[row][column]
                self.raw_switches[row][column] = raw
                if raw != self.candidate_switches[row][column]:
                    self.candidate_switches[row][column] = raw
                    self.candidate_counts[row][column] = 1
                elif self.candidate_counts[row][column] < config.BOOK_DEBOUNCE_SCANS:
                    self.candidate_counts[row][column] += 1
                if (
                    self.candidate_counts[row][column] >= config.BOOK_DEBOUNCE_SCANS
                    and self.switches[row][column] != raw
                ):
                    self.switches[row][column] = raw
                    changed_books.add(self._book_number(row, column))

        changed = False
        for book_number in sorted(changed_books):
            index = book_number - 1
            previous = self.book_states[index]
            current = self._book_state(book_number)
            self.book_states[index] = current
            if current != previous:
                self.events.append(("book", {
                    "book": book_number,
                    "state": current,
                    "previous": previous,
                    "in_closed": self._switch_closed(book_number, "in"),
                    "out_closed": self._switch_closed(book_number, "out"),
                }))
                changed = True
        return changed

    def command(self, name, data, now_ms):
        if name != "reset":
            return False
        self.switches = [[False] * self.COLUMN_COUNT for _ in range(self.ROW_COUNT)]
        self.candidate_switches = [[False] * self.COLUMN_COUNT for _ in range(self.ROW_COUNT)]
        self.candidate_counts = [[0] * self.COLUMN_COUNT for _ in range(self.ROW_COUNT)]
        self.book_states = ["unknown"] * self.BOOK_COUNT
        self.events.append(("reset", {}))
        return True

    def state(self):
        books = []
        for book_number in range(1, self.BOOK_COUNT + 1):
            books.append({
                "book": book_number,
                "state": self.book_states[book_number - 1],
                "in_closed": self._switch_closed(book_number, "in"),
                "out_closed": self._switch_closed(book_number, "out"),
            })
        return {
            "configured": self.configured,
            "scan_count": self.scan_count,
            "books": books,
            "switch_matrix": [list(row) for row in self.switches],
            "last_error": self.last_error,
        }

    def test_summary(self):
        rows = []
        for index, values in enumerate(self.switches):
            rows.append("W{}={}".format(
                index + 1,
                "".join("1" if closed else "0" for closed in values),
            ))
        books = []
        abbreviations = {"in": "I", "out": "O", "unknown": "?"}
        for index, state in enumerate(self.book_states):
            books.append("{}:{}".format(index + 1, abbreviations[state]))
        return "matrix {} | books {}".format(" ".join(rows), " ".join(books))

    def consume_events(self):
        events = self.events
        self.events = []
        return events

    def safe_defaults(self):
        for row in self.rows:
            row.init(Pin.IN)

    def _scan_matrix(self):
        readings = []
        for row_pin in self.rows:
            for row in self.rows:
                row.init(Pin.IN)
            row_pin.init(Pin.OUT, value=0 if config.BOOK_SWITCH_ACTIVE_LOW else 1)
            row_values = []
            for column in self.columns:
                value = bool(column.value())
                row_values.append(not value if config.BOOK_SWITCH_ACTIVE_LOW else value)
            readings.append(row_values)
            row_pin.init(Pin.IN)
        return readings

    def _make_column(self, pin_number):
        pull = Pin.PULL_UP if config.BOOK_SWITCH_ACTIVE_LOW else Pin.PULL_DOWN
        return Pin(pin_number, Pin.IN, pull)

    def _book_number(self, row, column):
        return column + 1 if row < 2 else column + 6

    def _switch_position(self, book_number, switch_name):
        column = (book_number - 1) % self.COLUMN_COUNT
        if book_number <= 5:
            row = 0 if switch_name == "in" else 1
        else:
            row = 2 if switch_name == "in" else 3
        return row, column

    def _switch_closed(self, book_number, switch_name):
        row, column = self._switch_position(book_number, switch_name)
        return self.switches[row][column]

    def _book_state(self, book_number):
        in_closed = self._switch_closed(book_number, "in")
        out_closed = self._switch_closed(book_number, "out")
        if in_closed and not out_closed:
            return "in"
        if out_closed and not in_closed:
            return "out"
        return "unknown"
