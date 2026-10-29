BOARD_ID = "mb-010"

# Direct VL53L0X sensors: Signal A = I2C SDA, Signal B = I2C SCL.
TOF_PORTS = {
    1: {
        "prop": "tof_1",
        "sensor": "TOF1",
        "i2c_id": 1,
        "near_threshold_mm": 300,
        "report_delta_mm": 50,
    },
    2: {
        "prop": "tof_2",
        "sensor": "TOF2",
        "i2c_id": 0,
        "near_threshold_mm": 300,
        "report_delta_mm": 50,
    },
}

# Hang the Dolls RFID PIBs: Signal A = wrong tag, Signal B = correct tag.
RFID_INPUT_PORTS = {
    5: {
        "prop": "doll_1",
        "reader": 1,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
    6: {
        "prop": "doll_2",
        "reader": 2,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
    7: {
        "prop": "doll_3",
        "reader": 3,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
}
SWITCH_INPUT_PORTS = {
    8: {
        "prop": "cross_on_symbols_2",
        "sensor": 2,
        "signal": "b",
        "active_value": 0,
        "pull": "up",
        "debounce_ms": 50,
    },
}
CANDLE_PORTS = {}
DEMON_KNOCKER_PORTS = {}
