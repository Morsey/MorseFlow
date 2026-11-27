__version__ = "1.0.0"

# DKE/XSRUPB FPC-8612 7.5-inch black/white/red panel on a Waveshare
# E-Paper Driver HAT Rev 2.3 (BS=0 / 4-line SPI, RESE=B).

DEBUG_REPL = True
DEBUG_BUFFER_SIZE = 50
BOOT_REPL_PAUSE_MS = 5000
BOOT_LED_TOGGLE_MS = 50
AUTO_RUN_MODULE = "app"
AUTO_RUN_FUNCTION = "main"

# Run the local clear/pattern/image/sleep test without starting networking.
DISPLAY_TEST_MODE = False

SITE = "prodigy"
ROOM = "cmcm"
DEVICE_ID = "epaper-001"
FIRMWARE_NAME = "epaper-display-pib"

SPI_BUS = 1
# Use software SPI while bringing up the Waveshare Rev 2.3/DKE combination.
# This keeps the same CLK and DIN pins but removes hardware-SPI configuration
# as a possible cause of commands not reaching the controller.
SPI_SOFTWARE = True
SPI_BAUDRATE = 500_000
SPI_POLARITY = 0
SPI_PHASE = 0

EPD_CS_PIN = 9
EPD_DC_PIN = 8
EPD_RST_PIN = 12
EPD_BUSY_PIN = 14
EPD_SCK_PIN = 10
EPD_MOSI_PIN = 11
# Rev 2.3 has a dedicated active-high power-control input.
EPD_PWR_PIN = 7
EPD_POWER_SETTLE_MS = 100

EPD_WIDTH = 800
EPD_HEIGHT = 480

DISPLAY_HOLD_MS = 5000
BUSY_TIMEOUT_MS = 120000

IMAGE_DIR = "images"
RESERVED_FREE_BYTES = 32768

NETWORK_DHCP = True
STATIC_IP = "192.168.10.61"
STATIC_SUBNET = "255.255.255.0"
STATIC_GATEWAY = "192.168.10.1"
STATIC_DNS = "192.168.10.1"

W5500_SPI_BUS = 0
W5500_SPI_BAUDRATE = 2_000_000
W5500_MISO_PIN = 16
W5500_CS_PIN = 17
W5500_SCK_PIN = 18
W5500_MOSI_PIN = 19
W5500_RESET_PIN = 20

HTTP_ENABLED = True
HTTP_PORT = 80

MQTT_ENABLED = True
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
