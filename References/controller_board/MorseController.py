from machine import Pin, SPI
import network
import utime
import ujson

try:
    from umqtt.simple import MQTTClient
except ImportError:
    try:
        from simple import MQTTClient
    except ImportError:
        MQTTClient = None


EXT_5V_PIN = 15  # Controls the external 5V supply for attached reader boards.

W5500_SPI_ID = 0
W5500_SCK_PIN = 18
W5500_MOSI_PIN = 19
W5500_MISO_PIN = 16
W5500_CS_PIN = 17
W5500_RST_PIN = 20

# One independent two-wire reader link per port. The two GPIOs are arbitrary
# controller pins; they are used as open-drain style CLK and DATA lines.
ACTIVE_PORTS = (3, 4, 5, 6, 7)
PORT_PINS = {
    1: {"clk": 2, "data": 3},
    2: {"clk": 4, "data": 5},
    3: {"clk": 6, "data": 7},
    4: {"clk": 8, "data": 9},
    5: {"clk": 10, "data": 11},
    6: {"clk": 12, "data": 26},
    7: {"clk": 13, "data": 27},
    8: {"clk": 14, "data": 28},
}

CMD_STATUS = 0x01
STATUS_FRAME_LENGTH = 24
MAGIC_0 = 0x4D  # M
MAGIC_1 = 0x52  # R
PROTOCOL_VERSION = 1

STATUS_FLAG_CARD_PRESENT = 0x01
STATUS_FLAG_READER_OK = 0x04
STATUS_FLAG_SCAN_ERROR = 0x08

POLL_INTERVAL_MS = 250
POWER_SETTLE_MS = 250
BIT_DELAY_US = 200
START_HOLD_US = 3000
ACK_TIMEOUT_US = 30000
RESPONSE_READY_US = 1000
READ_RETRIES = 3
DISCOVERY_READ_RETRIES = 1
RECOVERY_BIT_DELAY_US = BIT_DELAY_US
RECOVERY_START_HOLD_US = START_HOLD_US
RECOVERY_ACK_TIMEOUT_US = ACK_TIMEOUT_US
RECOVERY_RESPONSE_READY_US = RESPONSE_READY_US
RECOVERY_READ_RETRIES = 1
DISCOVERY_RECOVERY_INTERVAL = 20
DETACH_MISS_THRESHOLD = 10

MQTT_BROKER = "cmcm.local"
MQTT_PORT = 1883
MQTT_CLIENT_ID = b"mit-cmcm-rfid-controller"
MQTT_BASE_TOPIC = b"MIT/CMCM/rfidreader"
MQTT_KEEPALIVE_SECONDS = 30
NETWORK_CHECK_MS = 5000
MQTT_RECONNECT_MS = 5000
MQTT_STATUS_INTERVAL_MS = 30000
DEBUG_SUMMARY_INTERVAL_MS = 250
NETWORK_CONNECT_WAIT_MS = 0


def crc8(data, length):
    """CRC-8/ATM over the first length bytes."""
    crc = 0
    for i in range(length):
        crc ^= data[i]
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


class ReaderStatus:
    def __init__(self, frame):
        self.frame = frame
        self.flags = frame[3]
        self.sequence = frame[4]
        self.age_ms = frame[5] | (frame[6] << 8)
        self.uid_len = frame[7]
        self.card_count = frame[18]
        self.card_type = frame[19]
        self.error_code = frame[20]

        uid = frame[8:8 + self.uid_len]
        self.uid_hex = "".join("{:02X}".format(value) for value in uid)

    @property
    def reader_ok(self):
        return bool(self.flags & STATUS_FLAG_READER_OK)

    @property
    def card_present(self):
        return bool(self.flags & STATUS_FLAG_CARD_PRESENT)

    @property
    def scan_error(self):
        return bool(self.flags & STATUS_FLAG_SCAN_ERROR)


class TwoWireReaderPort:
    """Master side of the reader-board two-wire status link."""

    def __init__(self, port_number, clk_pin, data_pin, bit_delay_us=BIT_DELAY_US):
        self.port_number = port_number
        self.clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self.data = Pin(data_pin, Pin.IN, Pin.PULL_UP)
        self.bit_delay_us = bit_delay_us
        self.last_attached = None
        self.last_sequence = None
        self.last_uid_hex = None
        self.miss_count = 0
        self.current_status = None
        self.slow_recovery_count = 0
        self.release_lines()

    def release_clk(self):
        self.clk.init(Pin.IN, Pin.PULL_UP)

    def release_data(self):
        self.data.init(Pin.IN, Pin.PULL_UP)

    def drive_clk_low(self):
        self.clk.init(Pin.OUT)
        self.clk.value(0)

    def drive_data_low(self):
        self.data.init(Pin.OUT)
        self.data.value(0)

    def release_lines(self):
        self.release_data()
        self.release_clk()

    def _delay(self):
        utime.sleep_us(self.bit_delay_us)

    def _wait_data_low(self, timeout_us):
        start = utime.ticks_us()
        while self.data.value() != 0:
            if utime.ticks_diff(utime.ticks_us(), start) > timeout_us:
                return False
            utime.sleep_us(10)
        return True

    def _clock_high(self):
        self.release_clk()
        self._delay()

    def _clock_low(self):
        self.drive_clk_low()
        self._delay()

    def _write_bit(self, bit):
        if bit:
            self.release_data()
        else:
            self.drive_data_low()
        self._clock_high()
        self._clock_low()

    def _read_bit(self):
        self.release_data()
        self._clock_high()
        bit = 1 if self.data.value() else 0
        self._clock_low()
        return bit

    def _write_byte(self, value):
        for bit in range(7, -1, -1):
            self._write_bit(value & (1 << bit))

    def _read_byte(self):
        value = 0
        for _ in range(8):
            value = (value << 1) | self._read_bit()
        return value

    def read_frame(self, command=CMD_STATUS, bit_delay_us=None,
                   start_hold_us=START_HOLD_US,
                   ack_timeout_us=ACK_TIMEOUT_US,
                   response_ready_us=RESPONSE_READY_US):
        """Read one raw status frame, or return None when no reader responds."""
        old_bit_delay_us = self.bit_delay_us
        if bit_delay_us is not None:
            self.bit_delay_us = bit_delay_us
        try:
            self.release_lines()
            self._delay()

            # Start condition: DATA low while CLK is high, then pull CLK low
            # before sending the first command bit.
            self.drive_data_low()
            utime.sleep_us(start_hold_us)
            self._clock_low()

            self._write_byte(command)

            # ACK bit from reader. The reader pulls DATA low while the master
            # clocks the ACK cycle.
            self.release_data()
            self.release_clk()
            if not self._wait_data_low(ack_timeout_us):
                return None
            self._delay()
            self._clock_low()
            self.release_data()
            utime.sleep_us(response_ready_us)

            frame = bytearray(STATUS_FRAME_LENGTH)
            for i in range(STATUS_FRAME_LENGTH):
                frame[i] = self._read_byte()
            return frame
        finally:
            self.bit_delay_us = old_bit_delay_us
            self.release_lines()

    def _should_try_recovery_timing(self):
        if self.current_status:
            return True
        if self.miss_count < 3:
            return True
        return self.miss_count % DISCOVERY_RECOVERY_INTERVAL == 0

    def _read_status_recovery(self):
        if not self._should_try_recovery_timing():
            return None

        for _ in range(RECOVERY_READ_RETRIES):
            frame = self.read_frame(
                bit_delay_us=RECOVERY_BIT_DELAY_US,
                start_hold_us=RECOVERY_START_HOLD_US,
                ack_timeout_us=RECOVERY_ACK_TIMEOUT_US,
                response_ready_us=RECOVERY_RESPONSE_READY_US,
            )
            if valid_status_frame(frame):
                self.miss_count = 0
                self.slow_recovery_count += 1
                return ReaderStatus(frame)
            utime.sleep_ms(5)
        return None

    def read_status(self):
        attempts = READ_RETRIES if self.current_status else DISCOVERY_READ_RETRIES
        for _ in range(attempts):
            frame = self.read_frame()
            if valid_status_frame(frame):
                self.miss_count = 0
                return ReaderStatus(frame)
            utime.sleep_ms(5)
        return self._read_status_recovery()

    def poll_status(self):
        status = self.read_status()
        if status:
            self.current_status = status
            return status

        self.miss_count += 1
        if self.miss_count >= DETACH_MISS_THRESHOLD:
            self.current_status = None
        return self.current_status


def valid_status_frame(frame):
    if frame is None or len(frame) != STATUS_FRAME_LENGTH:
        return False
    if frame[0] != MAGIC_0 or frame[1] != MAGIC_1:
        return False
    if frame[2] != PROTOCOL_VERSION:
        return False
    if frame[7] > 10:
        return False
    if frame[22] != crc8(frame, 22):
        return False
    return True


def status_text(status):
    if status is None:
        return "not attached"
    if status.scan_error:
        return "scan error {}".format(status.error_code)
    if status.card_present and status.uid_hex:
        return "card {}".format(status.uid_hex)
    return "attached, no card"


def debug_port_text(port):
    status = port.current_status
    if status is None:
        return "P{}:--".format(port.port_number)

    suffix = ""
    if port.slow_recovery_count:
        suffix = " slow{}".format(port.slow_recovery_count)

    if status.scan_error:
        return "P{}:error{}{}".format(port.port_number, status.error_code, suffix)
    if status.card_present and status.uid_hex:
        return "P{}:{}{}".format(port.port_number, status.uid_hex, suffix)
    return "P{}:empty{}".format(port.port_number, suffix)


def debug_summary_text(reader_ports):
    return "Readers: " + " | ".join(debug_port_text(port) for port in reader_ports)


def print_debug_summary(reader_ports):
    print(debug_summary_text(reader_ports))


def should_report(port, attached, status):
    if attached != port.last_attached:
        return True
    if not attached:
        return False
    if status.sequence != port.last_sequence:
        return True
    if status.uid_hex != port.last_uid_hex:
        return True
    return False


def remember_status(port, attached, status):
    port.last_attached = attached
    if status:
        port.last_sequence = status.sequence
        port.last_uid_hex = status.uid_hex
    else:
        port.last_sequence = None
        port.last_uid_hex = None


def card_type_name(card_type):
    if card_type == 1:
        return "ISO14443"
    if card_type == 2:
        return "ISO15693"
    return "unknown"


def port_status_dict(port, status=None):
    if status is None:
        status = port.current_status

    if status is None:
        return {
            "port": port.port_number,
            "attached": False,
            "miss_count": port.miss_count,
        }

    return {
        "port": port.port_number,
        "attached": True,
        "reader_ok": status.reader_ok,
        "scan_error": status.scan_error,
        "error_code": status.error_code,
        "card_present": status.card_present,
        "card_count": status.card_count,
        "uid": status.uid_hex if status.card_present else "",
        "sequence": status.sequence,
        "age_ms": status.age_ms,
        "card_type": card_type_name(status.card_type),
        "miss_count": port.miss_count,
    }


def ports_summary(reader_ports):
    return {
        "type": "ports",
        "ports": [
            port_status_dict(port)
            for port in reader_ports
        ],
    }


def controller_status(reader_ports):
    return {
        "type": "controller",
        "network": {
            "connected": bool(network_iface and network_iface.isconnected()),
            "ifconfig": network_iface.ifconfig() if network_iface and network_iface.isconnected() else None,
        },
        "mqtt": {
            "connected": mqtt_client is not None,
            "broker": MQTT_BROKER,
        },
        "ports": ports_summary(reader_ports)["ports"],
    }


def mqtt_topic(suffix):
    if not suffix:
        return MQTT_BASE_TOPIC
    if isinstance(suffix, str):
        suffix = suffix.encode()
    return MQTT_BASE_TOPIC + b"/" + suffix


def mqtt_payload(data):
    return ujson.dumps(data)


def init_network():
    spi = SPI(
        W5500_SPI_ID,
        2_000_000,
        sck=Pin(W5500_SCK_PIN),
        mosi=Pin(W5500_MOSI_PIN),
        miso=Pin(W5500_MISO_PIN),
    )
    nic = network.WIZNET5K(spi, Pin(W5500_CS_PIN), Pin(W5500_RST_PIN))
    nic.active(True)
    return nic


def ensure_network(wait_ms=NETWORK_CONNECT_WAIT_MS):
    global network_iface, last_network_attempt_ms
    if network_iface and network_iface.isconnected():
        return True

    now = utime.ticks_ms()
    if utime.ticks_diff(now, last_network_attempt_ms) < NETWORK_CHECK_MS:
        return False
    last_network_attempt_ms = now

    try:
        if network_iface is None:
            network_iface = init_network()
        else:
            network_iface.active(True)

        start = utime.ticks_ms()
        while not network_iface.isconnected():
            if wait_ms <= 0 or utime.ticks_diff(utime.ticks_ms(), start) >= wait_ms:
                return False
            utime.sleep_ms(25)

        print("MorseController: network connected", network_iface.ifconfig())
        return True
    except Exception as e:
        print("MorseController: network error", e)
        network_iface = None
        return False


def mqtt_callback(topic, message):
    try:
        pending_mqtt_requests.append((topic, message))
    except Exception:
        pass


def ensure_mqtt():
    global mqtt_client, last_mqtt_attempt_ms
    if mqtt_client:
        if network_iface and network_iface.isconnected():
            return True
        mqtt_disconnect()
        return False
    if MQTTClient is None:
        return False
    if not ensure_network():
        return False

    now = utime.ticks_ms()
    if utime.ticks_diff(now, last_mqtt_attempt_ms) < MQTT_RECONNECT_MS:
        return False
    last_mqtt_attempt_ms = now

    try:
        client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, MQTT_PORT, keepalive=MQTT_KEEPALIVE_SECONDS)
        client.set_callback(mqtt_callback)
        client.connect(False)
        client.subscribe(mqtt_topic("request"))
        client.subscribe(mqtt_topic("request/#"))
        mqtt_client = client
        print("MorseController: MQTT connected", MQTT_BROKER)
        return True
    except Exception as e:
        print("MorseController: MQTT connect failed", e)
        mqtt_client = None
        return False


def mqtt_disconnect():
    global mqtt_client
    if mqtt_client:
        try:
            mqtt_client.disconnect()
        except Exception:
            pass
    mqtt_client = None


def mqtt_publish(topic, data, retain=False):
    if not mqtt_client:
        return False
    if not (network_iface and network_iface.isconnected()):
        mqtt_disconnect()
        return False
    try:
        mqtt_client.publish(topic, mqtt_payload(data), retain=retain)
        return True
    except Exception as e:
        print("MorseController: MQTT publish failed", e)
        mqtt_disconnect()
        return False


def service_mqtt():
    if not ensure_mqtt():
        return
    try:
        mqtt_client.check_msg()
    except Exception as e:
        print("MorseController: MQTT check failed", e)
        mqtt_disconnect()


def request_text(topic, message):
    topic_text = topic.decode() if isinstance(topic, bytes) else str(topic)
    message_text = message.decode().strip() if isinstance(message, bytes) else str(message).strip()
    request_prefix = (MQTT_BASE_TOPIC + b"/request").decode()
    if topic_text.startswith(request_prefix):
        suffix = topic_text[len(request_prefix):].strip("/")
        if suffix:
            return suffix
    return message_text


def handle_mqtt_requests(reader_ports_by_number):
    while pending_mqtt_requests:
        topic, message = pending_mqtt_requests.pop(0)
        request = request_text(topic, message)
        if request in ("", "all", "status"):
            mqtt_publish(mqtt_topic("status"), controller_status(list(reader_ports_by_number.values())))
        elif request in ("ports", "readers"):
            mqtt_publish(mqtt_topic("ports"), ports_summary(list(reader_ports_by_number.values())))
        elif request.startswith("port/"):
            publish_requested_port(reader_ports_by_number, request[5:])
        elif request.startswith("port "):
            publish_requested_port(reader_ports_by_number, request[5:])
        else:
            mqtt_publish(mqtt_topic("error"), {"error": "unknown request", "request": request})


def publish_requested_port(reader_ports_by_number, port_text):
    try:
        port_number = int(port_text)
    except ValueError:
        mqtt_publish(mqtt_topic("error"), {"error": "invalid port", "port": port_text})
        return

    port = reader_ports_by_number.get(port_number)
    if not port:
        mqtt_publish(mqtt_topic("error"), {"error": "unknown port", "port": port_number})
        return

    status = port.poll_status()
    mqtt_publish(mqtt_topic("ports/{}".format(port_number)), port_status_dict(port, status))


def publish_port_state(port, attached, status):
    mqtt_publish(mqtt_topic("ports/{}".format(port.port_number)), port_status_dict(port, status), retain=True)

    previous_uid = port.last_uid_hex if port.last_attached else None
    current_uid = status.uid_hex if status and status.card_present else None

    if previous_uid and previous_uid != current_uid:
        mqtt_publish(mqtt_topic("event"), {
            "event": "card_removed",
            "port": port.port_number,
            "uid": previous_uid,
        })

    if current_uid and current_uid != previous_uid:
        mqtt_publish(mqtt_topic("event"), {
            "event": "card_found",
            "port": port.port_number,
            "uid": current_uid,
            "card_type": card_type_name(status.card_type),
        })

    if port.last_attached is not None and port.last_attached != attached:
        mqtt_publish(mqtt_topic("event"), {
            "event": "reader_attached" if attached else "reader_detached",
            "port": port.port_number,
        })


network_iface = None
mqtt_client = None
pending_mqtt_requests = []
last_network_attempt_ms = -NETWORK_CHECK_MS
last_mqtt_attempt_ms = -MQTT_RECONNECT_MS
last_status_publish_ms = 0
last_debug_summary_ms = 0
last_debug_summary_text = ""


print("MorseController: booting controller")

ext_5v_pin = Pin(EXT_5V_PIN, Pin.OUT)
ext_5v_pin.on()
print("MorseController: ext 5V enabled")
utime.sleep_ms(POWER_SETTLE_MS)

reader_ports = []
reader_ports_by_number = {}
for port_number in ACTIVE_PORTS:
    pins = PORT_PINS[port_number]
    port = TwoWireReaderPort(port_number, pins["clk"], pins["data"])
    reader_ports.append(port)
    reader_ports_by_number[port_number] = port
    print(
        "MorseController: port {} enabled CLK={} DATA={}".format(
            port_number,
            pins["clk"],
            pins["data"],
        )
    )

if MQTTClient is None:
    print("MorseController: umqtt.simple is not available in this firmware")
last_status_publish_ms = utime.ticks_ms()

print("MorseController: polling reader ports")
while True:
    debug_summary_changed = False
    for port in reader_ports:
        status = port.poll_status()
        attached = status is not None
        if should_report(port, attached, status):
            publish_port_state(port, attached, status)
            remember_status(port, attached, status)
            debug_summary_changed = True

    now = utime.ticks_ms()
    summary_due = utime.ticks_diff(now, last_debug_summary_ms) >= DEBUG_SUMMARY_INTERVAL_MS
    summary_text = debug_summary_text(reader_ports)
    if (debug_summary_changed or summary_due) and summary_text != last_debug_summary_text:
        last_debug_summary_ms = now
        last_debug_summary_text = summary_text
        print(summary_text)

    if utime.ticks_diff(now, last_status_publish_ms) >= MQTT_STATUS_INTERVAL_MS:
        last_status_publish_ms = now
        mqtt_publish(mqtt_topic("status"), controller_status(reader_ports), retain=True)

    service_mqtt()
    handle_mqtt_requests(reader_ports_by_number)

    utime.sleep_ms(POLL_INTERVAL_MS)
