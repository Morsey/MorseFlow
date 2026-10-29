"""Standalone scanner for the MB6 ten-book reed-switch matrix."""

from machine import Pin
from time import sleep_ms


# GPIO0-GPIO4 are shared by Books 1-5 and Books 6-10.
COLUMN_PINS = (0, 1, 2, 3, 4)

# Row order matches the physical wiring.
ROW_PINS = (
    5,  # Shelf 1 out: Books 1-5
    6,  # Shelf 1 in:  Books 1-5
    7,  # Shelf 2 out: Books 6-10
    8,  # Shelf 2 in:  Books 6-10
)

DISCHARGE_MS = 10
SETTLE_MS = 10
SCAN_PAUSE_MS = 20
DEBOUNCE_SCANS = 3


def _all_columns_low(columns):
    for column in columns:
        column.init(Pin.OUT, value=0)


def _discharge_rows(rows):
    # All columns must already be low. Driving the rows low here safely clears
    # the high level retained by the board circuitry after a switch opens.
    for row in rows:
        row.init(Pin.OUT, value=0)
    sleep_ms(DISCHARGE_MS)
    for row in rows:
        row.init(Pin.IN, Pin.PULL_DOWN)


def _scan(columns, rows):
    readings = [[False] * 5 for _ in range(4)]

    for column_index, column in enumerate(columns):
        _all_columns_low(columns)
        _discharge_rows(rows)

        column.value(1)
        sleep_ms(SETTLE_MS)

        for row_index, row in enumerate(rows):
            readings[row_index][column_index] = bool(row.value())

        column.value(0)

    return readings


def _book_switches(readings, book_number):
    if book_number <= 5:
        column = 5 - book_number
        out_closed = readings[0][column]
        in_closed = readings[1][column]
    else:
        column = 10 - book_number
        out_closed = readings[2][column]
        in_closed = readings[3][column]
    return in_closed, out_closed


def _book_state(readings, book_number):
    in_closed, out_closed = _book_switches(readings, book_number)
    if in_closed and not out_closed:
        return "in"
    if out_closed and not in_closed:
        return "out"
    if not in_closed and not out_closed:
        return "between"
    return "both"


def _states(readings):
    return [_book_state(readings, number) for number in range(1, 11)]


def _print_all(states):
    print(
        "Books:",
        " ".join(
            "{}={}".format(number, state)
            for number, state in enumerate(states, 1)
        ),
    )


def main():
    columns = [Pin(number, Pin.OUT, value=0) for number in COLUMN_PINS]
    rows = [Pin(number, Pin.IN, Pin.PULL_DOWN) for number in ROW_PINS]

    stable = _scan(columns, rows)
    candidates = [row[:] for row in stable]
    counts = [[0] * 5 for _ in range(4)]
    previous_states = _states(stable)

    print("MB6 bookshelf matrix scanner")
    print("Press Ctrl-C to stop.")
    _print_all(previous_states)

    try:
        while True:
            readings = _scan(columns, rows)
            changed_books = set()

            for row_index in range(4):
                for column_index in range(5):
                    reading = readings[row_index][column_index]

                    if reading != candidates[row_index][column_index]:
                        candidates[row_index][column_index] = reading
                        counts[row_index][column_index] = 1
                    elif reading != stable[row_index][column_index]:
                        counts[row_index][column_index] += 1
                        if counts[row_index][column_index] >= DEBOUNCE_SCANS:
                            stable[row_index][column_index] = reading
                            counts[row_index][column_index] = 0
                            if row_index < 2:
                                changed_books.add(5 - column_index)
                            else:
                                changed_books.add(10 - column_index)
                    else:
                        counts[row_index][column_index] = 0

            if changed_books:
                current_states = _states(stable)
                for book_number in sorted(changed_books):
                    in_closed, out_closed = _book_switches(stable, book_number)
                    print(
                        "Book {}: {} -> {} (in={}, out={})".format(
                            book_number,
                            previous_states[book_number - 1],
                            current_states[book_number - 1],
                            int(in_closed),
                            int(out_closed),
                        )
                    )
                previous_states = current_states
                _print_all(previous_states)

            sleep_ms(SCAN_PAUSE_MS)
    finally:
        _all_columns_low(columns)
        for column in columns:
            column.init(Pin.IN)
        for row in rows:
            row.init(Pin.IN)
        print("Scanner stopped; GPIO0-GPIO8 left as inputs.")


if __name__ == "__main__":
    main()
