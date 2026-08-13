BOARD_ID = "mb-002"

# MB2 ports 1-5: Demon knockers. Signal A drives each solenoid; Signal B
# drives each NeoPixel data line directly from the Morseboard.
RFID_INPUT_PORTS = {}
CANDLE_PORTS = {}
DEMON_KNOCKER_PORTS = {
    1: {
        "prop": "demon_knocker_1",
        "knocker": 1,
        "pixel_count": 1,
        "solenoid_active_low": False,
    },
    2: {
        "prop": "demon_knocker_2",
        "knocker": 2,
        "pixel_count": 1,
        "solenoid_active_low": False,
    },
    3: {
        "prop": "demon_knocker_3",
        "knocker": 3,
        "pixel_count": 1,
        "solenoid_active_low": False,
    },
    4: {
        "prop": "demon_knocker_4",
        "knocker": 4,
        "pixel_count": 1,
        "solenoid_active_low": False,
    },
    5: {
        "prop": "demon_knocker_5",
        "knocker": 5,
        "pixel_count": 1,
        "solenoid_active_low": False,
    },
}
