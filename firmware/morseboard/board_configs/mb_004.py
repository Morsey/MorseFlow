BOARD_ID = "mb-004"
PROP_5V_ENABLED_AT_BOOT = True

RFID_INPUT_PORTS = {}

# Port 7 drives two magnetic door deadbolts. Each bolt remains locked while its
# output is held HIGH and releases when its output is LOW. Both default LOW.
OUTPUT_PORTS = {
    7: {
        "prop": "door_deadbolts",
        "signal_a": "door_AB",
        "signal_b": "door_BC",
        "initial_a": False,
        "initial_b": False,
    },
}

# Clock-face hardware test on port 8 Signal B. Inner LEDs 1-12 and outer LEDs
# 13-24 both map in order to clock positions 1-12.
# The MQTT-controlled chase test completes at 0.25 Hz. LEDs remain off at boot.
NEOPIXEL_CHASE_PORTS = {
    8: {
        "prop": "clock_puzzle",
        "signal": "b",
        "pixel_count": 24,
        "step_count": 12,
        "color": (0, 0, 255),
        "cycle_hz": 0.25,
    },
}
