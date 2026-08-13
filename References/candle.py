from machine import Pin
from utime import sleep_ms, ticks_add, ticks_diff, ticks_ms


BUTTON_ONE_PIN = 21
BUTTON_PRESSED_VALUE = 0
POWER_ENABLE_PIN = 15
TEST_PORT_COUNT = 2
PORT_DEFINITIONS = (
    {"candle": 2, "lit": 3},
    {"candle": 4, "lit": 5},
    {"candle": 6, "lit": 7},
    {"candle": 8, "lit": 9},
    {"candle": 10, "lit": 11},
    {"candle": 12, "lit": 26},
    {"candle": 13, "lit": 27},
    {"candle": 14, "lit": 28},
)
POLL_DELAY_MS = 20
CANDLE_ON_TIME_MS = 3000
STARTUP_FLASH_MS = 2000
SENSOR_TRIGGER_VALUE = 0
SENSOR_TRIGGER_LABEL = "LOW"
SENSOR_IDLE_LABEL = "HIGH"


def debug_pin_state(label, hardware, port, now_ms, turn_off_at_ms, candle_is_on):
    remaining_ms = 0
    if candle_is_on:
        remaining_ms = max(0, ticks_diff(turn_off_at_ms, now_ms))

    print(
        "candle debug: {} | lit_pin={} candle_pin={} power_pin={} candle_is_on={} remaining_ms={}".format(
            label,
            port["lit"].value(),
            port["candle"].value(),
            hardware["power_enable"].value(),
            candle_is_on,
            remaining_ms,
        )
    )


def create_hardware():
    return {
        "power_enable": Pin(POWER_ENABLE_PIN, Pin.OUT, value=1),
        "button_one": Pin(BUTTON_ONE_PIN, Pin.IN, Pin.PULL_UP),
        "ports": [
            {
                "number": index + 1,
                "candle": Pin(definition["candle"], Pin.OUT, value=0),
                "lit": Pin(definition["lit"], Pin.IN),
            }
            for index, definition in enumerate(PORT_DEFINITIONS[:TEST_PORT_COUNT])
        ],
    }


def run():
    hardware = create_hardware()
    hardware["power_enable"].value(1)
    ports = hardware["ports"]
    for port in ports:
        port["candle"].value(0)

    print("candle: hardware initialized")
    print("candle: 5V power is ON")
    print("candle: testing first {} ports".format(TEST_PORT_COUNT))
    print("candle: candle pins are OFF")
    print("candle: watching lit sensor pins")

    print("candle: flashing first {} candles for {} ms".format(TEST_PORT_COUNT, STARTUP_FLASH_MS))
    for port in ports:
        port["candle"].value(1)
    sleep_ms(STARTUP_FLASH_MS)
    for port in ports:
        port["candle"].value(0)
    print("candle: startup flash complete")

    states = []
    now_ms = ticks_ms()
    for port in ports:
        sensor_is_active = port["lit"].value() == SENSOR_TRIGGER_VALUE
        state = {
            "candle_is_on": False,
            "turn_off_at_ms": now_ms,
            "sensor_was_active": sensor_is_active,
            "armed_for_trigger": not sensor_is_active,
        }
        states.append(state)
        debug_pin_state(
            "startup port {}".format(port["number"]),
            hardware,
            port,
            now_ms,
            state["turn_off_at_ms"],
            state["candle_is_on"],
        )
        if not state["armed_for_trigger"]:
            print(
                "candle: port {} sensor is {} at startup, waiting for {} before enabling triggers".format(
                    port["number"],
                    SENSOR_TRIGGER_LABEL,
                    SENSOR_IDLE_LABEL,
                )
            )

    while True:
        now_ms = ticks_ms()
        for index, port in enumerate(ports):
            state = states[index]
            sensor_is_active = port["lit"].value() == SENSOR_TRIGGER_VALUE
            sensor_triggered_now = False

            if sensor_is_active != state["sensor_was_active"]:
                debug_pin_state(
                    "lit input changed port {}".format(port["number"]),
                    hardware,
                    port,
                    now_ms,
                    state["turn_off_at_ms"],
                    state["candle_is_on"],
                )
                if sensor_is_active:
                    if state["armed_for_trigger"]:
                        state["armed_for_trigger"] = False
                        sensor_triggered_now = True
                        print("candle: port {} sensor {} detected".format(port["number"], SENSOR_TRIGGER_LABEL))
                else:
                    state["armed_for_trigger"] = True
                    print("candle: port {} sensor {}, triggers enabled".format(port["number"], SENSOR_IDLE_LABEL))

            if sensor_triggered_now:
                state["turn_off_at_ms"] = ticks_add(now_ms, CANDLE_ON_TIME_MS)
                print(
                    "candle: port {} lit pin is {}, turning candle on for {} ms".format(
                        port["number"],
                        SENSOR_TRIGGER_LABEL,
                        CANDLE_ON_TIME_MS,
                    )
                )
                port["candle"].value(1)
                state["candle_is_on"] = True
                debug_pin_state(
                    "candle output set ON port {}".format(port["number"]),
                    hardware,
                    port,
                    now_ms,
                    state["turn_off_at_ms"],
                    state["candle_is_on"],
                )

            state["sensor_was_active"] = sensor_is_active

            if state["candle_is_on"] and ticks_diff(now_ms, state["turn_off_at_ms"]) >= 0:
                port["candle"].value(0)
                state["candle_is_on"] = False
                print("candle: port {} candle pin is OFF".format(port["number"]))
                debug_pin_state(
                    "candle output set OFF port {}".format(port["number"]),
                    hardware,
                    port,
                    now_ms,
                    state["turn_off_at_ms"],
                    state["candle_is_on"],
                )

        sleep_ms(POLL_DELAY_MS)


run()
