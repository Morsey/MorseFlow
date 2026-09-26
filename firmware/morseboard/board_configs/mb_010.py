BOARD_ID = "mb-010"

# Hang the Dolls RFID PIBs: Signal A = wrong tag, Signal B = correct tag.
RFID_INPUT_PORTS = {
    1: {
        "prop": "doll_1",
        "reader": 1,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
    2: {
        "prop": "doll_2",
        "reader": 2,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
    3: {
        "prop": "doll_3",
        "reader": 3,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
}
CANDLE_PORTS = {}
DEMON_KNOCKER_PORTS = {}
