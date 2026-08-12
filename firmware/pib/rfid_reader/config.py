CARD_TYPE = "ISO14443"
#CARD_TYPE = "ISO15693"
# PN5180 reader wiring from the original CMCM reader-board reference firmware.
PN5180_NSS_PIN = 2
PN5180_RST_PIN = 1
PN5180_BSY_PIN = 3
PN5180_SCK_PIN = 10
PN5180_MOSI_PIN = 11
PN5180_MISO_PIN = 12

# Local reader-board feedback.
NEOPIXEL_PIN = 13
NEOPIXEL_COUNT = 1

# Morseboard-facing status outputs.
# Correct high + wrong low: correct card present.
# Correct low + wrong high: wrong card present.
# Both low: no card.
STATUS_CORRECT_PIN = 26
STATUS_WRONG_PIN = 27

# Local card-list management buttons. Buttons are expected to pull the GPIO low.
ADD_BUTTON_PIN = 14
REMOVE_BUTTON_PIN = 29
BUTTON_ACTIVE_LOW = True
BUTTON_DEBOUNCE_MS = 40

POLL_INTERVAL_MS = 50
MISS_THRESHOLD = 3
CARD_STABLE_READS = 2
CARD_STABLE_WINDOW_MS = 1500
SCAN_ERROR_BACKOFF_MS = 1000
STATUS_LOG_INTERVAL_MS = 2000

CARD_STORE_PATH = "correct_cards.json"

# Used only when no stored card list exists yet. Once ADD, Remove, or clear is
# used, the persisted file becomes the source of truth.
DEFAULT_CORRECT_CARD_IDS = {
    "04AABBCCDD": "demo-key",
}

# Optional serial reporting mode. Prefer False unless bench debugging needs IDs.
SERIAL_REPORT_CARD_ID = False

# Keep this true while bringing up the first boards. It reports startup, state
# changes, and periodic no-card status without dumping every failed scan.
DEBUG_REPL = True
