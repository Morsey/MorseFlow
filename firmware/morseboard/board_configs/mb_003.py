BOARD_ID = "mb-003"

# Beasts RFID PIBs: Signal A = wrong tag, Signal B = correct tag.
RFID_INPUT_PORTS = {
    1: {"prop": "beasts_1", "reader": 1, "correct_signal": "b", "wrong_signal": "a"},
    2: {"prop": "beasts_2", "reader": 2, "correct_signal": "b", "wrong_signal": "a"},
    3: {"prop": "beasts_3", "reader": 3, "correct_signal": "b", "wrong_signal": "a"},
    4: {"prop": "beasts_4", "reader": 4, "correct_signal": "b", "wrong_signal": "a"},
}
SWITCH_INPUT_PORTS = {}
DUAL_SWITCH_INPUT_PORTS = {
    7: {
        "a": {
            "prop": "pull_cord",
            "sensor": "pull_cord",
            "active_value": 0,
            "pull": "up",
            "debounce_ms": 50,
        },
        "b": {
            "prop": "vampire_delay_switch",
            "sensor": "vampire_delay_switch",
            "active_value": 0,
            "pull": "up",
            "debounce_ms": 50,
        },
    },
}
CANDLE_PORTS = {}
DEMON_KNOCKER_PORTS = {}

# Port 5 drives two active-high latch locks. Pulse duration is capped in code
# even when a longer duration is requested over MQTT.
LATCH_LOCK_PULSE_MS = 100
LATCH_LOCK_MAX_PULSE_MS = 1000
LATCH_LOCK_PORTS = {
    5: {
        "prop": "latch_locks",
        "signal_a_lock": 2,
        "signal_b_lock": 13,
    },
    6: {
        "prop": "latch_locks",
        "signal_a_lock": 12,
    },
}
