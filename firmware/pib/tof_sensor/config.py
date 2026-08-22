TOF_SDA_PIN = 2
TOF_SCL_PIN = 3
TOF_ADDRESS = 0x29
I2C_FREQ = 100000

# Morseboard-facing status outputs.
# Near high + far low: object inside the configured threshold.
# Near low + far high: sensor healthy, no object inside threshold.
# Both low: idle/not ready.
# Both high: sensor error.
STATUS_NEAR_PIN = 26
STATUS_FAR_PIN = 27

POWER_ENABLE_PIN = None
NEOPIXEL_PIN = None
NEOPIXEL_COUNT = 1

POWER_SETTLE_MS = 500
SCAN_INTERVAL_MS = 1000
OUTPUT_PULSE_MS = 250
RANGE_INTERVAL_MS = 250
RANGE_TIMEOUT_MS = 1000
NEAR_THRESHOLD_MM = 300

DEBUG_REPL = True
