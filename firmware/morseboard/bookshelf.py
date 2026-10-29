from machine import Pin
from time import ticks_add, ticks_diff, ticks_ms

from debug import log


class BookshelfMatrix:
    ROW_COUNT = 4
    COLUMN_COUNT = 5
    BOOK_COUNT = 10

    def __init__(self, metadata):
        self.metadata = metadata or {}
        self.column_pin_numbers = tuple(self.metadata.get("column_pins", (0, 1, 2, 3, 4)))
        self.row_pin_numbers = tuple(self.metadata.get("row_pins", (5, 6, 7, 8)))
        if len(self.column_pin_numbers) != self.COLUMN_COUNT:
            raise ValueError("bookshelf matrix requires five column pins")
        if len(self.row_pin_numbers) != self.ROW_COUNT:
            raise ValueError("bookshelf matrix requires four row pins")

        self.discharge_ms = max(0, int(self.metadata.get("discharge_ms", 10)))
        self.settle_ms = max(0, int(self.metadata.get("settle_ms", 10)))
        self.debounce_scans = max(1, int(self.metadata.get("debounce_scans", 3)))
        self.columns = [Pin(number, Pin.OUT, value=0) for number in self.column_pin_numbers]
        self.rows = [Pin(number, Pin.OUT, value=0) for number in self.row_pin_numbers]

        self.column_index = 0
        self.phase = "discharge"
        self.deadline = ticks_add(ticks_ms(), self.discharge_ms)
        self.working = self._empty_matrix()
        self.stable = None
        self.candidates = self._empty_matrix()
        self.counts = [[0] * self.COLUMN_COUNT for _ in range(self.ROW_COUNT)]
        self.book_states = ["unknown"] * self.BOOK_COUNT
        log(
            "bookshelf",
            "matrix initialized columns={} rows={}".format(
                self.column_pin_numbers,
                self.row_pin_numbers,
            ),
        )

    def claimed_pins(self):
        return set(self.column_pin_numbers + self.row_pin_numbers)

    def update(self, now_ms):
        if ticks_diff(now_ms, self.deadline) < 0:
            return False, []

        if self.phase == "discharge":
            for row in self.rows:
                row.init(Pin.IN, Pin.PULL_DOWN)
            self.columns[self.column_index].value(1)
            self.phase = "settle"
            self.deadline = ticks_add(now_ms, self.settle_ms)
            return False, []

        for row_index, row in enumerate(self.rows):
            self.working[row_index][self.column_index] = bool(row.value())
        self.columns[self.column_index].value(0)

        if self.column_index < self.COLUMN_COUNT - 1:
            self.column_index += 1
            self._begin_discharge(now_ms)
            return False, []

        changed, events = self._finish_scan()
        self.column_index = 0
        self.working = self._empty_matrix()
        self._begin_discharge(now_ms)
        return changed, events

    def state(self):
        return {
            "prop": self.metadata.get("prop", "bookshelf"),
            "ready": self.stable is not None,
            "books": self.book_statuses(),
        }

    def book_statuses(self):
        statuses = []
        for book_number in range(1, self.BOOK_COUNT + 1):
            in_closed, out_closed = self._book_switches(book_number)
            statuses.append({
                "book": book_number,
                "state": self.book_states[book_number - 1],
                "in_closed": in_closed,
                "out_closed": out_closed,
            })
        return statuses

    def safe_defaults(self):
        for column in self.columns:
            column.init(Pin.OUT, value=0)
        for row in self.rows:
            row.init(Pin.OUT, value=0)
        self.column_index = 0
        self.phase = "discharge"
        self.deadline = ticks_add(ticks_ms(), self.discharge_ms)

    def _begin_discharge(self, now_ms):
        for column in self.columns:
            column.init(Pin.OUT, value=0)
        for row in self.rows:
            row.init(Pin.OUT, value=0)
        self.phase = "discharge"
        self.deadline = ticks_add(now_ms, self.discharge_ms)

    def _finish_scan(self):
        if self.stable is None:
            self.stable = [row[:] for row in self.working]
            self.candidates = [row[:] for row in self.working]
            self.book_states = [
                self._book_state(book_number)
                for book_number in range(1, self.BOOK_COUNT + 1)
            ]
            log("bookshelf", "initial scan complete")
            return True, []

        changed_books = set()
        for row_index in range(self.ROW_COUNT):
            for column_index in range(self.COLUMN_COUNT):
                reading = self.working[row_index][column_index]
                if reading != self.candidates[row_index][column_index]:
                    self.candidates[row_index][column_index] = reading
                    self.counts[row_index][column_index] = 1
                elif reading != self.stable[row_index][column_index]:
                    self.counts[row_index][column_index] += 1
                    if self.counts[row_index][column_index] >= self.debounce_scans:
                        self.stable[row_index][column_index] = reading
                        self.counts[row_index][column_index] = 0
                        changed_books.add(
                            5 - column_index if row_index < 2 else 10 - column_index
                        )
                else:
                    self.counts[row_index][column_index] = 0

        events = []
        for book_number in sorted(changed_books):
            previous = self.book_states[book_number - 1]
            current = self._book_state(book_number)
            self.book_states[book_number - 1] = current
            in_closed, out_closed = self._book_switches(book_number)
            event = {
                "prop": self.metadata.get("prop", "bookshelf"),
                "book": book_number,
                "state": current,
                "previous": previous,
                "in_closed": in_closed,
                "out_closed": out_closed,
            }
            events.append(event)
            log("bookshelf", "book {} {} -> {}".format(book_number, previous, current))
        return bool(events), events

    def _book_switches(self, book_number):
        if self.stable is None:
            return False, False
        if book_number <= 5:
            column = 5 - book_number
            out_closed = self.stable[0][column]
            in_closed = self.stable[1][column]
        else:
            column = 10 - book_number
            out_closed = self.stable[2][column]
            in_closed = self.stable[3][column]
        return in_closed, out_closed

    def _book_state(self, book_number):
        in_closed, out_closed = self._book_switches(book_number)
        if in_closed and not out_closed:
            return "in"
        if out_closed and not in_closed:
            return "out"
        if not in_closed and not out_closed:
            return "between"
        return "both"

    def _empty_matrix(self):
        return [[False] * self.COLUMN_COUNT for _ in range(self.ROW_COUNT)]
