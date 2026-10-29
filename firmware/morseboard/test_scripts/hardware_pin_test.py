"""Morseboard GPIO output pulse test.

Copy this file to the board filesystem root alongside pins.py, then run it from
the MicroPython REPL:

    import hardware_pin_test
    hardware_pin_test.main()

The script enables switched 5V prop power, then repeatedly pulses each RJ45
port Signal A and Signal B so LEDs, meters, optos, or attached PIB indicators
can be checked by eye.
"""

from machine import Pin
from time import sleep_ms

import pins


PULSE_MS = 300
GAP_MS = 150
PORT_GAP_MS = 350
ROUND_GAP_MS = 1000
POWER_SETTLE_MS = 500

TEST_PROP_POWER = True
TEST_OPTIONAL_RELAY = True


def _pin(pin_number, initial=0):
    pin = Pin(pin_number, Pin.OUT)
    pin.value(initial)
    return pin


def _all_off(port_pins, relay=None):
    for signal_a, signal_b in port_pins:
        signal_a.value(0)
        signal_b.value(0)
    if relay is not None:
        relay.value(0)


def _pulse(label, pin, duration_ms=PULSE_MS):
    print(label, "ON")
    pin.value(1)
    sleep_ms(duration_ms)
    pin.value(0)
    print(label, "off")
    sleep_ms(GAP_MS)


def _pulse_group(label, group, duration_ms=PULSE_MS):
    print(label, "ON")
    for pin in group:
        pin.value(1)
    sleep_ms(duration_ms)
    for pin in group:
        pin.value(0)
    print(label, "off")
    sleep_ms(GAP_MS)


def main(repeat=True):
    print("Morseboard GPIO output pulse test")
    print("Press Ctrl-C to stop; all tested outputs will be set low.")

    prop_power = None
    relay = None
    if TEST_PROP_POWER:
        prop_power = _pin(pins.PROP_POWER_ENABLE, initial=1)
        print("Switched 5V prop power enabled on GPIO{}".format(
            pins.PROP_POWER_ENABLE,
        ))
        sleep_ms(POWER_SETTLE_MS)

    if TEST_OPTIONAL_RELAY:
        relay = _pin(pins.OPTIONAL_RELAY)

    port_pins = [
        (_pin(signal_a), _pin(signal_b))
        for signal_a, signal_b in pins.PORT_PINS
    ]
    all_a = [pair[0] for pair in port_pins]
    all_b = [pair[1] for pair in port_pins]
    all_signals = all_a + all_b

    try:
        while True:
            _all_off(port_pins, relay)

            for index, (signal_a, signal_b) in enumerate(port_pins, start=1):
                signal_a_number, signal_b_number = pins.PORT_PINS[index - 1]
                print("Port", index)
                _pulse("  Signal A GPIO{}".format(signal_a_number), signal_a)
                _pulse("  Signal B GPIO{}".format(signal_b_number), signal_b)
                sleep_ms(PORT_GAP_MS)

            _pulse_group("All Signal A pins", all_a)
            _pulse_group("All Signal B pins", all_b)
            _pulse_group("All port signal pins", all_signals)

            if relay is not None:
                _pulse("Optional relay GPIO{}".format(pins.OPTIONAL_RELAY), relay)

            print("Round complete")
            if not repeat:
                break
            sleep_ms(ROUND_GAP_MS)
    finally:
        _all_off(port_pins, relay)
        if prop_power is not None:
            prop_power.value(0)
            print("Switched 5V prop power disabled")
        print("Hardware pin test stopped")


if __name__ == "__main__":
    main()
