BOARD_ID = "mb-007"
MQTT_ENABLED = True
DFPLAYER_ENABLED = True
CANDLE_STARTUP_PULSE_MS = 0
CANDLE_AUTO_TRIGGER_ENABLED = False
CANDLE_TRIGGER_ON_ACTIVE = False

CANDLE_PORTS = {
    1: {
        "prop": "candle_1",
        "candle": 1,
    },
    2: {
        "prop": "candle_2",
        "candle": 2,
    },
    3: {
        "prop": "candle_3",
        "candle": 3,
    },
}

RFID_INPUT_PORTS = {}

# BCDoor distance sensor on port 4 (Signal A = I2C0 SDA, Signal B = I2C0 SCL).
TOF_PORTS = {
    4: {
        "prop": "bc_door",
        "sensor": "BCDoor",
        "i2c_id": 0,
        "near_threshold_mm": 300,
        "report_delta_mm": 50,
    },
}

# Single latch-lock controller on port 5, Signal A.
LATCH_LOCK_PORTS = {
    5: {
        "prop": "latch_lock",
        "signal_a_lock": 1,
    },
}
