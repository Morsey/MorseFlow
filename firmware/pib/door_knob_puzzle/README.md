# DoorKnobPuzzle PIB

Standalone networked puzzle controller for a W5500-EVB-Pico2-class board. It
uses the same Ethernet and MQTT conventions as the Morseboard firmware, but has
an independent GPIO configuration and controller.

## Current State

The networking, MQTT, and first puzzle controller are ready. The matrix uses
GPIO0-GPIO3 for row wires 1-4 and GPIO4-GPIO8 for column wires 5-9.

The code in `References/Knobbyknob/` is reference material only. It is not
imported or uploaded as part of this firmware.

## MQTT

Default topic root:

```text
morseflow/prodigy/cmcm/door-knob-puzzle-001
```

Networking is currently paused for local hardware testing with
`MQTT_ENABLED = False` in `config.py`. The app conditionally imports its
network modules, so it can run on a standard MicroPython build without the
`network` module. Set the option to `True` after flashing W5500-enabled
MicroPython.

While networking is disabled, the USB REPL prints book changes immediately and
prints a matrix summary once per second. For example:

```text
[test] matrix W1=10000 W2=00000 W3=00000 W4=00001 | books 1:I 2:? 3:? 4:? 5:? 6:? 7:? 8:? 9:? 10:O
```

Each five-character row is ordered by wires 5-9. `1` means the switch is
closed, `0` means open, `I` means the book is in, `O` means out, and `?` means
both or neither switch is closed.

Published topics:

- `.../status` — retained availability, IP, uptime, and current state.
- `.../state` — retained puzzle state.
- `.../event` — debounced book-state, reset, and error events.

Subscribed commands:

- `.../cmd/status` with `{}` republishes status and state.
- `.../cmd/reset` with `{}` clears the debounced book states and rescans them.

## Book Matrix

Twenty switches are arranged as four row wires by five column wires:

| Row wire | Switches |
| --- | --- |
| 1 | Books 1-5 `in` |
| 2 | Books 1-5 `out` |
| 3 | Books 6-10 `in` |
| 4 | Books 6-10 `out` |

Column wires 5-9 correspond respectively to Books 1/6, 2/7, 3/8, 4/9,
and 5/10. The matrix is scanned every 20 ms by default. A reading must remain
the same for three scans before it is accepted.

A book reports `in` when only its `in` switch is closed, `out` when only its
`out` switch is closed, and `unknown` when both or neither are closed.

Important: a passive switch matrix can produce ghost closures when several
switches are closed simultaneously. Each switch needs an isolation diode, or
the PCB needs equivalent isolation, for every combination to be distinguishable.

## GPIO Configuration

Tuple order matches the physical wire-number order shown here:

```python
BOOK_ROW_PINS = (0, 1, 2, 3)       # Wires 1-4
BOOK_COLUMN_PINS = (4, 5, 6, 7, 8) # Wires 5-9
```

Do not assign GPIO16-GPIO20 to puzzle hardware unless the Ethernet wiring is
also changed; those pins are configured for the W5500.

## Upload

Upload every `.py` file from this directory to the board filesystem root. Use
the W5500-enabled MicroPython build for the target board. At startup, press
Ctrl-C during the five-second LED-flash window to remain at the USB REPL.
