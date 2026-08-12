BOARD_ID = "mb-001"

# MB1 RFID PIB wiring currently has Signal A = wrong card and Signal B = correct card.
RFID_INPUT_PORTS = {
    3: {
        "prop": "demon_seal_1",
        "reader": 1,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
    4: {
        "prop": "demon_seal_2",
        "reader": 2,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
    5: {
        "prop": "demon_seal_3",
        "reader": 3,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
    6: {
        "prop": "demon_seal_4",
        "reader": 4,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
    7: {
        "prop": "demon_seal_5",
        "reader": 5,
        "correct_signal": "b",
        "wrong_signal": "a",
    },
}
