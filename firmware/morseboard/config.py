SITE = "prodigy"
ROOM = "cmcm"
BOARD_ID = "mb-unconfigured"

DEBUG_REPL = True
DEBUG_BUFFER_SIZE = 50
BOOT_REPL_PAUSE_MS = 5000
BOOT_LED_TOGGLE_MS = 50
APP_LED_TOGGLE_MS = 500

MQTT_HOST = "cmcm.local"
MQTT_PORT = 1883
MQTT_USERNAME = None
MQTT_PASSWORD = None
MQTT_KEEPALIVE_SECONDS = 30
MQTT_ENABLED = True
MQTT_QOS = 1

NETWORK_DHCP = True

# Used only when NETWORK_DHCP is False.
STATIC_IP = "192.168.10.51"
STATIC_SUBNET = "255.255.255.0"
STATIC_GATEWAY = "192.168.10.1"
STATIC_DNS = "192.168.10.1"

RECONNECT_INTERVAL_MS = 5000
STATUS_INTERVAL_MS = 30000
APP_LOOP_ERROR_BACKOFF_MS = 1000
NETWORK_WAIT_LOG_INTERVAL_MS = 5000

PROP_5V_ENABLED_AT_BOOT = True
RELAY_ENABLED_AT_BOOT = False
PORT_SIGNALS_HIGH_AT_BOOT = False

# Per-board config can override any uppercase setting above.
# For a deployed board, copy one file from board_configs/ to board_config.py.
RFID_INPUT_PORTS = {}
CANDLE_PORTS = {}
DEMON_KNOCKER_PORTS = {}
CANDLE_ON_TIME_MS = 3000
CANDLE_STARTUP_PULSE_MS = 0
CANDLE_TRIGGER_ON_ACTIVE = False
CANDLE_SENSOR_TRIGGER_VALUE = 0
DEMON_KNOCKER_PULSE_MS = 120


def _load_board_config():
    try:
        import board_config
    except ImportError:
        return

    for name in dir(board_config):
        if name.isupper():
            globals()[name] = getattr(board_config, name)


_load_board_config()

TOPIC_ROOT = "morseflow/{}/{}/{}".format(SITE, ROOM, BOARD_ID)
