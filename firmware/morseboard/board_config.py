BOARD_ID = "mb-006"
MQTT_ENABLED = True
REPL_EVENT_LOGGING = False
DFPLAYER_ENABLED = False
PROP_POWER_CONTROL_ENABLED = False

RFID_INPUT_PORTS = {}
SWITCH_INPUT_PORTS = {}
CANDLE_PORTS = {}
DEMON_KNOCKER_PORTS = {}

# Books 1-5 and 6-10 share GPIO0-GPIO4 in reversed physical order: columns
# 0-4 map to Books 5/10, 4/9, 3/8, 2/7, and 1/6. The row pins identify shelf
# and position: GPIO5 shelf 1 out, GPIO6 shelf 1 in, GPIO7 shelf 2 out, and
# GPIO8 shelf 2 in. The discharge phase is required because the input-side
# board circuitry otherwise retains a high level after a reed switch opens.
BOOKSHELF_MATRIX = {
    "prop": "bookshelf",
    "column_pins": (0, 1, 2, 3, 4),
    "row_pins": (5, 6, 7, 8),
    "discharge_ms": 10,
    "settle_ms": 10,
    "debounce_scans": 3,
}

# AS5600 safe-dial puzzle on the special MB6 screw terminals. Rotation is
# evaluated locally; MQTT receives only meaningful puzzle events. A saved
# doorknob_config.json, written by cmd/doorknob/config with save=true, overrides
# the combination settings below after restart.
DOORKNOB_PUZZLE = {
    "prop": "door_knob",
    "i2c_id": 1,
    "sda_pin": 10,
    "scl_pin": 11,
    "frequency": 10000,
    "address": 0x36,
    "poll_ms": 50,
    "tolerance_degrees": 10.0,
    "target_overturn_degrees": 15.0,
    "direction_deadband_degrees": 1.5,
    "clockwise_sign": 1,
    "auto_reset_ms": 2000,
    "config_path": "doorknob_config.json",
    "sequence": (
        {"target": 0, "direction": "cw", "min_travel": 0},
        {"target": 180, "direction": "ccw", "min_travel": 90},
        {"target": 90, "direction": "cw", "min_travel": 45},
        {"target": 180, "direction": "ccw", "min_travel": 45},
        {"target": 270, "direction": "cw", "min_travel": 45},
    ),
}
