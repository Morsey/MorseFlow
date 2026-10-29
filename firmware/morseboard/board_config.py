BOARD_ID = "mb-003"

# Beasts RFID PIBs: Signal A = wrong tag, Signal B = correct tag.
RFID_INPUT_PORTS = {
    1: {"prop": "beasts_1", "reader": 1, "correct_signal": "b", "wrong_signal": "a"},
    2: {"prop": "beasts_2", "reader": 2, "correct_signal": "b", "wrong_signal": "a"},
    3: {"prop": "beasts_3", "reader": 3, "correct_signal": "b", "wrong_signal": "a"},
    4: {"prop": "beasts_4", "reader": 4, "correct_signal": "b", "wrong_signal": "a"},
}
SWITCH_INPUT_PORTS = {}
CANDLE_PORTS = {}
DEMON_KNOCKER_PORTS = {}
