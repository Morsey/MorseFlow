BOARD_ID = "mb-004"

RFID_INPUT_PORTS = {}

# One blue pixel advances from 1 through 12 on port 1 Signal A. The complete
# chase repeats at 0.25 Hz (one four-second cycle).
NEOPIXEL_CHASE_PORTS = {
    1: {
        "prop": "blue_pixel_chase",
        "signal": "a",
        "pixel_count": 12,
        "color": (0, 0, 255),
        "cycle_hz": 0.25,
    },
}
