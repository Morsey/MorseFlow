"""Pulse GPIO2 at startup and whenever GPIO3 goes low.

Copy this file to the board filesystem root, then run:

    import gpio2_trigger_test
    gpio2_trigger_test.main()

GPIO2 is Port 1 Signal A and GPIO3 is Port 1 Signal B.
"""

from machine import Pin
from time import sleep_ms


OUTPUT_PIN = 2
TRIGGER_PIN = 3
PULSE_MS = 200
POLL_MS = 10


def pulse(output):
    output.value(1)
    sleep_ms(PULSE_MS)
    output.value(0)


def main():
    output = Pin(OUTPUT_PIN, Pin.OUT, value=0)
    trigger = Pin(TRIGGER_PIN, Pin.IN, Pin.PULL_UP)

    print("Pulsing GPIO{} for {} ms".format(OUTPUT_PIN, PULSE_MS))
    try:
        pulse(output)

        print("Monitoring GPIO{}; press Ctrl-C to stop".format(TRIGGER_PIN))
        was_high = bool(trigger.value())

        while True:
            is_high = bool(trigger.value())
            if was_high and not is_high:
                print("GPIO{} went low; pulsing GPIO{}".format(
                    TRIGGER_PIN,
                    OUTPUT_PIN,
                ))
                pulse(output)

            was_high = is_high
            sleep_ms(POLL_MS)
    except KeyboardInterrupt:
        print("Test stopped")
    finally:
        output.value(0)


if __name__ == "__main__":
    main()
