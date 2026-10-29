DEBUG_REPL = True
DEBUG_BUFFER_SIZE = 50
BOOT_REPL_PAUSE_MS = 5000
BOOT_LED_TOGGLE_MS = 50
APP_LED_TOGGLE_MS = 500
AUTO_RUN_MODULE = "app"
AUTO_RUN_FUNCTION = "main"

SITE = "prodigy"
ROOM = "cmcm"
DEVICE_ID = "door-knob-puzzle-001"
FIRMWARE_NAME = "door-knob-puzzle-pib"

# Four row wires and five column wires form the 20-switch book matrix. Tuple
# order follows the physical wire numbers.
BOOK_ROW_PINS = (0, 1, 2, 3)       # Wires 1, 2, 3, 4
BOOK_COLUMN_PINS = (4, 5, 6, 7, 8) # Wires 5, 6, 7, 8, 9

# The scanner drives one row low and reads columns with pull-ups. A closed
# switch therefore reads low. Change this only if the interface electronics
# invert the signals.
BOOK_SWITCH_ACTIVE_LOW = True
BOOK_SCAN_INTERVAL_MS = 20
BOOK_DEBOUNCE_SCANS = 3
BOOK_TEST_LOG_INTERVAL_MS = 1000

NETWORK_DHCP = True
STATIC_IP = "192.168.10.62"
STATIC_SUBNET = "255.255.255.0"
STATIC_GATEWAY = "192.168.10.1"
STATIC_DNS = "192.168.10.1"

# Standard W5500-EVB-Pico/Pico2 wiring used by MorseFlow.
W5500_SPI_BUS = 0
W5500_SPI_BAUDRATE = 2_000_000
W5500_MISO_PIN = 16
W5500_CS_PIN = 17
W5500_SCK_PIN = 18
W5500_MOSI_PIN = 19
W5500_RESET_PIN = 20

# Local hardware-test mode. Set True after installing W5500-enabled
# MicroPython and connecting the board to the network.
MQTT_ENABLED = False
MQTT_HOST = "cmcm.local"
MQTT_PORT = 1883
MQTT_USERNAME = None
MQTT_PASSWORD = None
MQTT_KEEPALIVE_SECONDS = 30
MQTT_QOS = 1

RECONNECT_INTERVAL_MS = 5000
STATUS_INTERVAL_MS = 30000
NETWORK_WAIT_LOG_INTERVAL_MS = 5000
APP_LOOP_ERROR_BACKOFF_MS = 1000

TOPIC_ROOT = "morseflow/{}/{}/{}".format(SITE, ROOM, DEVICE_ID)
