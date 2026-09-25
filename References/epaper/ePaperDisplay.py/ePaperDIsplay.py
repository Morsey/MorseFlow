"""Network-controlled Waveshare 7.3-inch seven-color e-paper display.

Copyright (c) 2026 Rob Morse, Morse Immersive Technologies

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

This single MicroPython file runs on a W5500-EVB-Pico. It:

* Connects to Ethernet using DHCP.
* Runs a small webserver for uploading, deleting, and selecting .bin images.
* Connects to an MQTT broker for remote display commands and status messages.
* Streams 800 x 480, seven-color image buffers to the e-paper panel.

The display stores two 4-bit pixels in each byte, so each full-screen image is
800 * 480 / 2 = 192000 bytes.
"""

import gc
import os

try:
    import ujson as json
except ImportError:
    import json

try:
    import usocket as socket
except ImportError:
    import socket

try:
    import network
except ImportError:
    network = None

from machine import Pin, SPI
from utime import sleep_ms, ticks_diff, ticks_ms


# Logging levels:
# 0 = quiet, 1 = essential lifecycle messages, 2 = detailed debugging.
LOG_LEVEL = 1
LOG_INFO = 1
LOG_DEBUG = 2
BOOT_DELAY_MS = 5000


def log(level, *parts):
    if LOG_LEVEL >= level:
        print(*parts)


# ---------------------------------------------------------------------------
# Hardware and network configuration
# ---------------------------------------------------------------------------

# E-paper display SPI pins. These use SPI1 and avoid the W5500 Ethernet pins.
SPI_BUS = 1
SPI_BAUDRATE = 1_000_000
CS_PIN = 9
DC_PIN = 8
RST_PIN = 12
BUSY_PIN = 13
SCK_PIN = 10
MOSI_PIN = 11

WIDTH = 800
HEIGHT = 480
BUFFER_SIZE = WIDTH * HEIGHT // 2
ROW_SIZE = WIDTH // 2
DEFAULT_IMAGE_PATH = "landscape.bin"
DISPLAY_HOLD_MS = 5000

# W5500 Ethernet pins on the W5500-EVB-Pico. These are fixed by the board.
ETH_SPI_BUS = 0
ETH_SPI_BAUDRATE = 2_000_000
ETH_MISO_PIN = 16
ETH_CS_PIN = 17
ETH_SCK_PIN = 18
ETH_MOSI_PIN = 19
ETH_RST_PIN = 20

HTTP_PORT = 80
MQTT_SERVER = "cmcm.local"
MQTT_CLIENT_ID = "w5500-epaper-display"
MQTT_TOPIC_PREFIX = b"MIT/CMCM/epaperdisplay/"
HEARTBEAT_INTERVAL_MS = 60000
NETWORK_CHECK_INTERVAL_MS = 2000
NETWORK_RETRY_INTERVAL_MS = 5000
MQTT_RETRY_INTERVAL_MS = 5000
RESERVED_FREE_BYTES = 32768

# The e-paper panel understands these seven packed pixel values.
BLACK = 0x0
WHITE = 0x1
GREEN = 0x2
BLUE = 0x3
RED = 0x4
YELLOW = 0x5
ORANGE = 0x6

_BYTE = bytearray(1)

FONT_5X7 = {
    " ": (0x00, 0x00, 0x00, 0x00, 0x00),
    "-": (0x08, 0x08, 0x08, 0x08, 0x08),
    ".": (0x00, 0x00, 0x00, 0x00, 0x40),
    ":": (0x00, 0x10, 0x00, 0x10, 0x00),
    "0": (0x3E, 0x51, 0x49, 0x45, 0x3E),
    "1": (0x00, 0x42, 0x7F, 0x40, 0x00),
    "2": (0x42, 0x61, 0x51, 0x49, 0x46),
    "3": (0x21, 0x41, 0x45, 0x4B, 0x31),
    "4": (0x18, 0x14, 0x12, 0x7F, 0x10),
    "5": (0x27, 0x45, 0x45, 0x45, 0x39),
    "6": (0x3C, 0x4A, 0x49, 0x49, 0x30),
    "7": (0x01, 0x71, 0x09, 0x05, 0x03),
    "8": (0x36, 0x49, 0x49, 0x49, 0x36),
    "9": (0x06, 0x49, 0x49, 0x29, 0x1E),
    "A": (0x7E, 0x11, 0x11, 0x11, 0x7E),
    "B": (0x7F, 0x49, 0x49, 0x49, 0x36),
    "C": (0x3E, 0x41, 0x41, 0x41, 0x22),
    "D": (0x7F, 0x41, 0x41, 0x22, 0x1C),
    "E": (0x7F, 0x49, 0x49, 0x49, 0x41),
    "F": (0x7F, 0x09, 0x09, 0x09, 0x01),
    "G": (0x3E, 0x41, 0x49, 0x49, 0x7A),
    "H": (0x7F, 0x08, 0x08, 0x08, 0x7F),
    "I": (0x00, 0x41, 0x7F, 0x41, 0x00),
    "J": (0x20, 0x40, 0x41, 0x3F, 0x01),
    "K": (0x7F, 0x08, 0x14, 0x22, 0x41),
    "L": (0x7F, 0x40, 0x40, 0x40, 0x40),
    "M": (0x7F, 0x02, 0x0C, 0x02, 0x7F),
    "N": (0x7F, 0x04, 0x08, 0x10, 0x7F),
    "O": (0x3E, 0x41, 0x41, 0x41, 0x3E),
    "P": (0x7F, 0x09, 0x09, 0x09, 0x06),
    "Q": (0x3E, 0x41, 0x51, 0x21, 0x5E),
    "R": (0x7F, 0x09, 0x19, 0x29, 0x46),
    "S": (0x46, 0x49, 0x49, 0x49, 0x31),
    "T": (0x01, 0x01, 0x7F, 0x01, 0x01),
    "U": (0x3F, 0x40, 0x40, 0x40, 0x3F),
    "V": (0x1F, 0x20, 0x40, 0x20, 0x1F),
    "W": (0x7F, 0x20, 0x18, 0x20, 0x7F),
    "X": (0x63, 0x14, 0x08, 0x14, 0x63),
    "Y": (0x07, 0x08, 0x70, 0x08, 0x07),
    "Z": (0x61, 0x51, 0x49, 0x45, 0x43),
}


# ---------------------------------------------------------------------------
# Low-level e-paper display driver
# ---------------------------------------------------------------------------

def init_spi():
    spi = SPI(
        SPI_BUS,
        baudrate=SPI_BAUDRATE,
        sck=Pin(SCK_PIN),
        mosi=Pin(MOSI_PIN),
    )
    cs = Pin(CS_PIN, Pin.OUT, value=1)
    dc = Pin(DC_PIN, Pin.OUT, value=0)
    rst = Pin(RST_PIN, Pin.OUT, value=1)
    busy = Pin(BUSY_PIN, Pin.IN, Pin.PULL_UP)
    return spi, cs, dc, rst, busy


def pulse_reset(rst):
    rst(1)
    sleep_ms(20)
    rst(0)
    sleep_ms(2)
    rst(1)
    sleep_ms(20)


def pack_color(color):
    return (color << 4) | color


class EPD7in3F:
    """Driver for the Waveshare 7.3-inch seven-color e-paper panel."""

    def __init__(self):
        self.spi, self.cs, self.dc, self.rst, self.busy = init_spi()

    def write_byte(self, value):
        _BYTE[0] = value
        self.spi.write(_BYTE)

    def command(self, value):
        self.dc(0)
        self.cs(0)
        self.write_byte(value)
        self.cs(1)

    def data(self, value):
        self.dc(1)
        self.cs(0)
        if isinstance(value, int):
            self.write_byte(value)
        else:
            self.spi.write(value)
        self.cs(1)

    def data_repeat(self, value, count, chunk_size=1024):
        chunk = bytearray(min(chunk_size, count))
        for index in range(len(chunk)):
            chunk[index] = value

        self.dc(1)
        self.cs(0)
        while count:
            write_len = min(len(chunk), count)
            if write_len == len(chunk):
                self.spi.write(chunk)
            else:
                self.spi.write(memoryview(chunk)[:write_len])
            count -= write_len
        self.cs(1)

    def wait_until_idle(self, timeout_ms=120000):
        start = ticks_ms()
        while self.busy.value() == 0:
            if ticks_diff(ticks_ms(), start) > timeout_ms:
                raise RuntimeError("e-paper busy timeout")
            sleep_ms(5)
        return ticks_diff(ticks_ms(), start)

    def init(self):
        log(LOG_INFO, "epaper: init")
        pulse_reset(self.rst)
        self.wait_until_idle()
        sleep_ms(30)

        self.command(0xAA)
        self.data(0x49)
        self.data(0x55)
        self.data(0x20)
        self.data(0x08)
        self.data(0x09)
        self.data(0x18)

        self.command(0x01)
        self.data(0x3F)
        self.data(0x00)
        self.data(0x32)
        self.data(0x2A)
        self.data(0x0E)
        self.data(0x2A)

        self.command(0x00)
        self.data(0x5F)
        self.data(0x69)

        self.command(0x03)
        self.data(0x00)
        self.data(0x54)
        self.data(0x00)
        self.data(0x44)

        self.command(0x05)
        self.data(0x40)
        self.data(0x1F)
        self.data(0x1F)
        self.data(0x2C)

        self.command(0x06)
        self.data(0x6F)
        self.data(0x1F)
        self.data(0x1F)
        self.data(0x22)

        self.command(0x08)
        self.data(0x6F)
        self.data(0x1F)
        self.data(0x1F)
        self.data(0x22)

        self.command(0x13)
        self.data(0x00)
        self.data(0x04)

        self.command(0x30)
        self.data(0x3C)

        self.command(0x41)
        self.data(0x00)

        self.command(0x50)
        self.data(0x3F)

        self.command(0x60)
        self.data(0x02)
        self.data(0x00)

        self.command(0x61)
        self.data(0x03)
        self.data(0x20)
        self.data(0x01)
        self.data(0xE0)

        self.command(0x82)
        self.data(0x1E)

        self.command(0x84)
        self.data(0x00)

        self.command(0x86)
        self.data(0x00)

        self.command(0xE3)
        self.data(0x2F)

        self.command(0xE0)
        self.data(0x00)

        self.command(0xE6)
        self.data(0x00)

        log(LOG_INFO, "epaper: ready")

    def display(self, buffer):
        if len(buffer) != BUFFER_SIZE:
            raise ValueError("buffer must be %d bytes" % BUFFER_SIZE)
        self.command(0x10)
        self.data(buffer)
        self.refresh()

    def display_file(self, path, chunk_size=1024):
        total = 0
        chunk = bytearray(chunk_size)

        log(LOG_DEBUG, "epaper: checking image file", path)
        with open(path, "rb") as file:
            file.seek(0, 2)
            size = file.tell()
        if size != BUFFER_SIZE:
            raise ValueError("image file must be %d bytes" % BUFFER_SIZE)
        log(LOG_DEBUG, "epaper: image file size ok", size, "bytes")

        log(LOG_INFO, "epaper: display image", path)
        self.command(0x10)
        self.dc(1)
        self.cs(0)
        try:
            with open(path, "rb") as file:
                while True:
                    count = file.readinto(chunk)
                    if not count:
                        break
                    if count == chunk_size:
                        self.spi.write(chunk)
                    else:
                        self.spi.write(chunk[:count])
                    total += count
                    if total % 24576 == 0:
                        log(LOG_DEBUG, "epaper: streamed", total, "bytes")
        finally:
            self.cs(1)
        log(LOG_DEBUG, "epaper: image data streamed", total, "bytes")

        self.refresh()

    def clear(self, color=WHITE):
        packed = pack_color(color)
        self.command(0x10)
        self.data_repeat(packed, BUFFER_SIZE)
        self.refresh()

    def refresh(self):
        log(LOG_DEBUG, "epaper: power on")
        self.command(0x04)
        log(LOG_DEBUG, "epaper: power on done", self.wait_until_idle(), "ms")
        log(LOG_INFO, "epaper: refresh")
        self.command(0x12)
        self.data(0x00)
        log(LOG_INFO, "epaper: refresh done", self.wait_until_idle(), "ms")
        log(LOG_DEBUG, "epaper: power off")
        self.command(0x02)
        self.data(0x00)
        log(LOG_DEBUG, "epaper: power off done", self.wait_until_idle(), "ms")

    def sleep(self):
        self.command(0x07)
        self.data(0xA5)
        sleep_ms(2000)


def probe():
    spi, cs, dc, rst, busy = init_spi()
    pulse_reset(rst)
    log(LOG_DEBUG, "epaper: reset complete")
    log(LOG_DEBUG, "epaper: busy pin value", busy.value())

    dc(0)
    cs(0)
    spi.write(b"\x00")
    cs(1)
    log(LOG_DEBUG, "epaper: SPI write test complete")


def run_init():
    epd = EPD7in3F()
    epd.init()


def send_test_image():
    epd = EPD7in3F()
    epd.init()
    epd.clear(WHITE)
    log(LOG_INFO, "epaper: test image sent")


def show_raw_image(path="image.bin"):
    epd = EPD7in3F()
    epd.init()
    epd.display_file(path)
    log(LOG_INFO, "epaper: raw image sent")


def show_then_clear(path=DEFAULT_IMAGE_PATH, hold_ms=DISPLAY_HOLD_MS):
    log(LOG_INFO, "epaper: show then clear")
    epd = EPD7in3F()
    epd.init()

    log(LOG_INFO, "epaper: displaying image", path)
    epd.display_file(path)
    log(LOG_INFO, "epaper: image shown")

    log(LOG_INFO, "epaper: holding image for", hold_ms, "ms")
    sleep_ms(hold_ms)

    log(LOG_INFO, "epaper: clearing screen to white")
    epd.clear(WHITE)
    log(LOG_INFO, "epaper: screen cleared")

    epd.sleep()
    log(LOG_INFO, "epaper: display put to sleep")


def send_color_bars():
    epd = EPD7in3F()
    epd.init()

    colors = (BLACK, WHITE, GREEN, BLUE, RED, YELLOW, ORANGE)
    bar_width = WIDTH // len(colors)
    row = bytearray(ROW_SIZE)

    for x in range(0, WIDTH, 2):
        left = colors[min(x // bar_width, len(colors) - 1)]
        right = colors[min((x + 1) // bar_width, len(colors) - 1)]
        row[x // 2] = (left << 4) | right

    epd.command(0x10)
    epd.dc(1)
    epd.cs(0)
    for _ in range(HEIGHT):
        epd.spi.write(row)
    epd.cs(1)

    epd.refresh()
    log(LOG_INFO, "epaper: color bars sent")


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def fit_text_scale(text, max_width, preferred_scale):
    scale = preferred_scale
    while scale > 1 and text_width(text, scale) > max_width:
        scale -= 1
    return scale


def fill_x_range(row, x0, x1, color):
    if x1 <= 0 or x0 >= WIDTH:
        return
    x0 = max(0, x0)
    x1 = min(WIDTH, x1)

    if x0 & 1:
        index = x0 // 2
        row[index] = (row[index] & 0xF0) | color
        x0 += 1

    if x1 & 1:
        x1 -= 1
        index = x1 // 2
        row[index] = (row[index] & 0x0F) | (color << 4)

    packed = pack_color(color)
    for index in range(x0 // 2, x1 // 2):
        row[index] = packed


def clear_row(row, color):
    packed = pack_color(color)
    for index in range(len(row)):
        row[index] = packed


def draw_text_row(row, text, left, top, scale, color, y):
    text_y = y - top
    if text_y < 0 or text_y >= 7 * scale:
        return

    glyph_y = text_y // scale
    cursor = left
    for char in text:
        glyph = FONT_5X7.get(char, FONT_5X7[" "])
        for col in range(5):
            if glyph[col] & (1 << glyph_y):
                x0 = cursor + col * scale
                fill_x_range(row, x0, x0 + scale, color)
        cursor += 6 * scale


def send_text(line1="DISPLAY!", line2="READY"):
    epd = EPD7in3F()
    epd.init()

    line1 = line1.upper()
    line2 = line2.upper()
    line1_scale = fit_text_scale(line1, WIDTH - 160, 10)
    line2_scale = fit_text_scale(line2, WIDTH - 260, 8)
    line1_x = (WIDTH - text_width(line1, line1_scale)) // 2
    line2_x = (WIDTH - text_width(line2, line2_scale)) // 2
    line1_y = 140
    line2_y = 275
    row = bytearray(ROW_SIZE)

    log(LOG_DEBUG, "epaper: sending image data")
    epd.command(0x10)
    epd.dc(1)
    epd.cs(0)
    for y in range(HEIGHT):
        clear_row(row, WHITE)

        if 18 <= y < HEIGHT - 18:
            if y < 28 or y >= HEIGHT - 28:
                fill_x_range(row, 18, WIDTH - 18, BLUE)
            else:
                fill_x_range(row, 18, 28, BLUE)
                fill_x_range(row, WIDTH - 28, WIDTH - 18, BLUE)

        if 105 <= y < 260:
            fill_x_range(row, 70, WIDTH - 70, YELLOW)

        if 290 <= y < 380:
            fill_x_range(row, 250, WIDTH - 250, GREEN)

        draw_text_row(row, line1, line1_x, line1_y, line1_scale, BLACK, y)
        draw_text_row(row, line2, line2_x, line2_y, line2_scale, RED, y)
        epd.spi.write(row)
        if y and y % 80 == 0:
            log(LOG_DEBUG, "epaper: sent row", y)
    epd.cs(1)
    log(LOG_DEBUG, "epaper: image data sent")

    epd.refresh()
    log(LOG_INFO, "epaper: text sent")


# ---------------------------------------------------------------------------
# Small utility helpers
# ---------------------------------------------------------------------------

def ticks_due(now, last, interval):
    return ticks_diff(now, last) >= interval


def url_decode(value):
    value = value.replace("+", " ")
    result = ""
    index = 0
    while index < len(value):
        if value[index] == "%" and index + 2 < len(value):
            try:
                result += chr(int(value[index + 1:index + 3], 16))
                index += 3
                continue
            except ValueError:
                pass
        result += value[index]
        index += 1
    return result


def parse_query(path):
    if "?" not in path:
        return path, {}
    path, query = path.split("?", 1)
    values = {}
    for item in query.split("&"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
        else:
            key, value = item, ""
        values[url_decode(key)] = url_decode(value)
    return path, values


def safe_image_name(name):
    # Keep filenames simple because they are used directly on the Pico's
    # filesystem. This prevents paths such as "../main.py".
    name = url_decode(name).strip()
    if not name or "/" in name or "\\" in name or ".." in name:
        raise ValueError("bad image name")
    if not name.endswith(".bin"):
        raise ValueError("image must end with .bin")
    for char in name:
        if not (
            "0" <= char <= "9"
            or "A" <= char <= "Z"
            or "a" <= char <= "z"
            or char in "._-"
        ):
            raise ValueError("bad image name")
    return name


def fs_free_bytes():
    # statvfs reports filesystem blocks. Free bytes are block size * free blocks.
    stat = os.statvfs("/")
    return stat[0] * stat[3]


def file_size(path):
    stat = os.stat(path)
    return stat[6]


def list_images():
    images = []
    for name in os.listdir():
        if name.endswith(".bin"):
            try:
                images.append((name, file_size(name)))
            except OSError:
                pass
    images.sort()
    return images


def json_bytes(value):
    return json.dumps(value).encode()


def socket_readline(sock):
    # MicroPython sockets do not always provide readline(), so read one byte at
    # a time until the HTTP header line ends.
    line = bytearray()
    while True:
        char = sock.recv(1)
        if not char:
            break
        line.append(char[0])
        if char == b"\n":
            break
    return bytes(line)


def http_send(client, status, content_type=b"text/plain", body=b""):
    if isinstance(status, str):
        status = status.encode()
    if isinstance(content_type, str):
        content_type = content_type.encode()
    if isinstance(body, str):
        body = body.encode()
    client.send(b"HTTP/1.1 " + status + b"\r\n")
    client.send(b"Connection: close\r\n")
    client.send(b"Content-Type: " + content_type + b"\r\n")
    client.send(b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n")
    if body:
        client.send(body)


def http_json(client, status, data):
    http_send(client, status, b"application/json", json_bytes(data))


# ---------------------------------------------------------------------------
# Minimal MQTT client
# ---------------------------------------------------------------------------

def mqtt_encode_length(length):
    encoded = bytearray()
    while True:
        byte = length & 0x7F
        length >>= 7
        if length:
            byte |= 0x80
        encoded.append(byte)
        if not length:
            return encoded


def mqtt_read_exact(sock, count):
    data = bytearray()
    while len(data) < count:
        chunk = sock.recv(count - len(data))
        if not chunk:
            raise OSError("mqtt socket closed")
        data.extend(chunk)
    return bytes(data)


def mqtt_read_length(sock):
    multiplier = 1
    value = 0
    while True:
        byte = mqtt_read_exact(sock, 1)[0]
        value += (byte & 0x7F) * multiplier
        if not (byte & 0x80):
            return value
        multiplier *= 128
        if multiplier > 128 * 128 * 128:
            raise ValueError("bad mqtt length")


def socket_send_all(sock, data):
    try:
        sock.sendall(data)
    except AttributeError:
        total = 0
        while total < len(data):
            sent = sock.send(data[total:])
            if not sent:
                raise OSError("socket send failed")
            total += sent


def mqtt_string(value):
    if not isinstance(value, bytes):
        value = value.encode()
    return bytes((len(value) >> 8, len(value) & 0xFF)) + value


def mqtt_u16(value):
    return bytes((value >> 8, value & 0xFF))


class MQTTClient:
    def __init__(self, client_id, server, port=1883, keepalive=30):
        self.client_id = client_id if isinstance(client_id, bytes) else client_id.encode()
        self.server = server
        self.port = port
        self.keepalive = keepalive
        self.sock = None
        self.callback = None
        self.packet_id = 1
        self.last_io = ticks_ms()
        self.last_ping = 0
        self.ping_outstanding = False

    def set_callback(self, callback):
        self.callback = callback

    def connect(self):
        addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        sock = socket.socket()
        try:
            sock.connect(addr)
            sock.settimeout(5)

            variable = mqtt_string(b"MQTT") + b"\x04\x02"
            variable += mqtt_u16(self.keepalive)
            payload = mqtt_string(self.client_id)
            packet = b"\x10" + mqtt_encode_length(len(variable) + len(payload))
            socket_send_all(sock, packet + variable + payload)

            response = mqtt_read_exact(sock, 4)
            if response[0] != 0x20 or response[1] != 0x02 or response[3] != 0:
                raise OSError("mqtt connect refused")

            sock.settimeout(0)
            self.sock = sock
            self.last_io = ticks_ms()
            self.last_ping = 0
            self.ping_outstanding = False
        except Exception:
            try:
                sock.close()
            except Exception:
                pass
            raise

    def disconnect(self):
        if self.sock:
            try:
                socket_send_all(self.sock, b"\xe0\x00")
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
        self.sock = None

    def _next_packet_id(self):
        packet_id = self.packet_id
        self.packet_id += 1
        if self.packet_id > 65535:
            self.packet_id = 1
        return packet_id

    def subscribe(self, topic):
        if not isinstance(topic, bytes):
            topic = topic.encode()
        packet_id = self._next_packet_id()
        variable = mqtt_u16(packet_id) + mqtt_string(topic) + b"\x00"
        packet = b"\x82" + mqtt_encode_length(len(variable)) + variable
        socket_send_all(self.sock, packet)
        self.last_io = ticks_ms()

    def publish(self, topic, payload):
        if not isinstance(topic, bytes):
            topic = topic.encode()
        if not isinstance(payload, bytes):
            payload = payload.encode()
        variable = mqtt_string(topic) + payload
        packet = b"\x30" + mqtt_encode_length(len(variable)) + variable
        socket_send_all(self.sock, packet)
        self.last_io = ticks_ms()

    def ping(self):
        socket_send_all(self.sock, b"\xc0\x00")
        self.last_io = ticks_ms()
        self.last_ping = self.last_io
        self.ping_outstanding = True

    def check_msg(self):
        now = ticks_ms()
        if self.ping_outstanding and ticks_due(now, self.last_ping, 10000):
            raise OSError("mqtt keepalive timeout")
        if not self.ping_outstanding and ticks_due(now, self.last_io, self.keepalive * 500):
            self.ping()

        try:
            first = self.sock.recv(1)
        except OSError:
            return
        if not first:
            raise OSError("mqtt socket closed")

        try:
            self.sock.settimeout(2)
            remaining = mqtt_read_length(self.sock)
            payload = mqtt_read_exact(self.sock, remaining)
            self.last_io = ticks_ms()
            self.ping_outstanding = False
        finally:
            self.sock.settimeout(0)
        packet_type = first[0] >> 4

        if packet_type == 3:
            topic_len = (payload[0] << 8) | payload[1]
            topic = payload[2:2 + topic_len]
            message = payload[2 + topic_len:]
            if self.callback:
                self.callback(topic, message)
        elif packet_type == 9:
            log(LOG_DEBUG, "mqtt: subscribe acknowledged")
        elif packet_type == 13:
            log(LOG_DEBUG, "mqtt: ping response")


class EpaperApp:
    """Main application: network, webserver, MQTT, filesystem, and display."""

    def __init__(self):
        self.epd = EPD7in3F()
        self.nic = None
        self.http = None
        self.mqtt = None
        self.current = None
        self.busy = False
        self.pending = None
        self.started_at = ticks_ms()
        self.last_heartbeat = ticks_ms() - HEARTBEAT_INTERVAL_MS
        self.last_network_check = ticks_ms() - NETWORK_CHECK_INTERVAL_MS
        self.last_network_attempt = ticks_ms() - NETWORK_RETRY_INTERVAL_MS
        self.last_mqtt_attempt = ticks_ms() - MQTT_RETRY_INTERVAL_MS
        self.network_was_up = False

    def status(self, message="ok"):
        # Status is used by the web API, MQTT status topic, and heartbeat.
        uptime_ms = ticks_diff(ticks_ms(), self.started_at)
        return {
            "message": message,
            "busy": self.busy,
            "current": self.current,
            "free": fs_free_bytes(),
            "images": [name for name, size in list_images()],
            "ip": self.ip_address(),
            "network": self.network_connected(),
            "mqtt": self.mqtt is not None,
            "uptime_ms": uptime_ms,
            "uptime_s": uptime_ms // 1000,
        }

    def ip_address(self):
        if self.nic:
            try:
                return self.nic.ifconfig()[0]
            except Exception:
                pass
        return None

    def publish(self, topic, data):
        if not self.mqtt:
            return
        try:
            if not isinstance(topic, bytes):
                topic = topic.encode()
            if not isinstance(data, bytes):
                data = json_bytes(data)
            self.mqtt.publish(MQTT_TOPIC_PREFIX + topic, data)
        except Exception as err:
            log(LOG_INFO, "mqtt: publish failed", err)
            self.close_mqtt()

    def publish_status(self, message="ok"):
        data = self.status(message)
        log(LOG_DEBUG, "status:", data)
        self.publish(b"status", data)

    def close_http(self):
        if self.http:
            try:
                self.http.close()
            except Exception:
                pass
        self.http = None

    def close_mqtt(self):
        if self.mqtt:
            try:
                self.mqtt.disconnect()
            except Exception:
                pass
        self.mqtt = None

    def network_connected(self):
        if not self.nic:
            return False
        try:
            return self.nic.isconnected()
        except Exception:
            return False

    def connect_network(self):
        if network is None:
            raise RuntimeError("network module not available")

        self.close_mqtt()
        self.close_http()

        log(LOG_INFO, "net: starting W5500 DHCP")
        spi = SPI(
            ETH_SPI_BUS,
            baudrate=ETH_SPI_BAUDRATE,
            sck=Pin(ETH_SCK_PIN),
            mosi=Pin(ETH_MOSI_PIN),
            miso=Pin(ETH_MISO_PIN),
        )
        self.nic = network.WIZNET5K(spi, Pin(ETH_CS_PIN), Pin(ETH_RST_PIN))
        self.nic.active(True)
        try:
            self.nic.ifconfig("dhcp")
        except Exception as err:
            log(LOG_DEBUG, "net: dhcp request method skipped", err)

        start = ticks_ms()
        while not self.nic.isconnected():
            if ticks_diff(ticks_ms(), start) > 30000:
                raise RuntimeError("network DHCP timeout")
            log(LOG_INFO, "net: waiting for DHCP")
            sleep_ms(1000)
        log(LOG_INFO, "net: connected", self.nic.ifconfig())
        self.network_was_up = True
        self.last_network_check = ticks_ms()

    def reset_network(self):
        log(LOG_INFO, "net: resetting network sockets")
        self.close_mqtt()
        self.close_http()
        if self.nic:
            try:
                self.nic.active(False)
            except Exception:
                pass
        self.nic = None
        self.network_was_up = False

    def ensure_network(self):
        # Called from the main loop. It keeps Ethernet, HTTP, and MQTT alive
        # after cable pulls, switch restarts, or broker/network outages.
        now = ticks_ms()
        if self.nic and self.network_was_up and not ticks_due(
            now, self.last_network_check, NETWORK_CHECK_INTERVAL_MS
        ):
            return True
        self.last_network_check = now

        if self.network_connected():
            if not self.network_was_up:
                log(LOG_INFO, "net: link restored", self.nic.ifconfig())
                self.network_was_up = True
            if not self.http:
                try:
                    self.start_http()
                except Exception as err:
                    log(LOG_INFO, "http: restart failed", err)
                    self.close_http()
            return True

        if self.network_was_up:
            log(LOG_INFO, "net: link lost")
            self.reset_network()

        if not ticks_due(now, self.last_network_attempt, NETWORK_RETRY_INTERVAL_MS):
            return False

        self.last_network_attempt = now
        try:
            self.connect_network()
            self.start_http()
            self.connect_mqtt(force=True)
            self.publish_status("network reconnected")
            return True
        except Exception as err:
            log(LOG_INFO, "net: reconnect failed", err)
            self.reset_network()
            return False

    def start_http(self):
        self.close_http()
        self.http = socket.socket()
        self.http.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.http.bind(("0.0.0.0", HTTP_PORT))
        self.http.listen(1)
        self.http.settimeout(0)
        log(LOG_INFO, "http: listening on port", HTTP_PORT)

    def connect_mqtt(self, force=False):
        if not self.network_connected():
            return
        now = ticks_ms()
        if self.mqtt and not force:
            return
        if not force and not ticks_due(now, self.last_mqtt_attempt, MQTT_RETRY_INTERVAL_MS):
            return
        self.last_mqtt_attempt = now
        self.close_mqtt()
        client = None
        try:
            log(LOG_INFO, "mqtt: connecting to", MQTT_SERVER)
            client = MQTTClient(MQTT_CLIENT_ID, MQTT_SERVER, keepalive=30)
            client.set_callback(self.on_mqtt_message)
            client.connect()
            client.subscribe(MQTT_TOPIC_PREFIX)
            client.subscribe(MQTT_TOPIC_PREFIX + b"command")
            client.subscribe(MQTT_TOPIC_PREFIX + b"commands")
            self.mqtt = client
            log(LOG_INFO, "mqtt: connected")
            self.publish_status("mqtt connected")
        except Exception as err:
            log(LOG_INFO, "mqtt: connect failed", err)
            if client:
                try:
                    client.disconnect()
                except Exception:
                    pass
            self.mqtt = None

    def on_mqtt_message(self, topic, payload):
        log(LOG_DEBUG, "mqtt: received", topic, payload)
        if topic in (
            MQTT_TOPIC_PREFIX + b"status",
            MQTT_TOPIC_PREFIX + b"heartbeat",
        ):
            log(LOG_DEBUG, "mqtt: ignoring own status topic", topic)
            return
        try:
            command = json.loads(payload)
            self.queue_command(command, "mqtt")
        except Exception as err:
            self.publish_status("bad mqtt command: %s" % err)

    def queue_command(self, command, source):
        # Commands can arrive from MQTT or the web API. They are queued so the
        # slow e-paper refresh happens in one place in the main loop.
        action = command.get("action", command.get("command", "")).lower()
        if action == "show":
            image = safe_image_name(command.get("image", ""))
            self.pending = ("show", image)
        elif action in ("white", "blank", "clear"):
            self.pending = ("color", WHITE)
        elif action == "black":
            self.pending = ("color", BLACK)
        elif action == "delete":
            image = safe_image_name(command.get("image", ""))
            self.delete_image(image)
            return
        elif action == "list":
            self.publish_status("list")
            return
        else:
            raise ValueError("unknown action")
        self.publish_status("queued from %s" % source)

    def process_pending(self):
        # E-paper refreshes can take many seconds. While one is active, mark the
        # app busy so status/heartbeat messages accurately describe the board.
        if not self.pending or self.busy:
            return
        action, value = self.pending
        self.pending = None
        self.busy = True
        gc.collect()
        try:
            if action == "show":
                self.publish_status("displaying %s" % value)
                self.epd.display_file(value)
                self.current = value
                self.publish_status("displayed %s" % value)
            elif action == "color":
                color_name = "white" if value == WHITE else "black"
                self.publish_status("displaying %s" % color_name)
                self.epd.clear(value)
                self.current = color_name
                self.publish_status("displayed %s" % color_name)
        except Exception as err:
            log(LOG_INFO, "display: action failed", err)
            self.publish_status("display failed: %s" % err)
        finally:
            self.busy = False
            gc.collect()

    def delete_image(self, name):
        name = safe_image_name(name)
        log(LOG_INFO, "files: deleting", name)
        os.remove(name)
        if self.current == name:
            self.current = None
        self.publish_status("deleted %s" % name)

    def upload_image(self, client, name, content_length):
        # The browser uploads the raw .bin file body. This avoids multipart
        # parsing and lets us stream directly to flash without using much RAM.
        name = safe_image_name(name)
        if content_length != BUFFER_SIZE:
            raise ValueError("upload must be %d bytes" % BUFFER_SIZE)
        if fs_free_bytes() < content_length + RESERVED_FREE_BYTES:
            raise OSError("not enough free space")

        tmp_name = name + ".tmp"
        remaining = content_length
        written = 0
        chunk_size = 1024
        try:
            with open(tmp_name, "wb") as file:
                while remaining:
                    chunk = client.recv(min(chunk_size, remaining))
                    if not chunk:
                        raise OSError("upload interrupted")
                    file.write(chunk)
                    written += len(chunk)
                    remaining -= len(chunk)
        except Exception:
            try:
                os.remove(tmp_name)
            except OSError:
                pass
            raise
        try:
            os.remove(name)
        except OSError:
            pass
        os.rename(tmp_name, name)
        log(LOG_INFO, "files: uploaded", name, written, "bytes")
        self.publish_status("uploaded %s" % name)

    def handle_http(self):
        if not self.http or not self.network_connected():
            return
        try:
            client, addr = self.http.accept()
        except OSError:
            return
        log(LOG_DEBUG, "http: connection", addr)
        client.settimeout(5)
        try:
            self.handle_http_client(client)
        except Exception as err:
            log(LOG_INFO, "http: error", err)
            try:
                http_json(client, b"500 Internal Server Error", {"error": str(err)})
            except Exception:
                pass
        finally:
            client.close()

    def handle_http_client(self, client):
        # Minimal HTTP parser. It only implements the routes this device needs:
        # status, image listing, raw uploads, deletes, and display commands.
        line = socket_readline(client)
        if not line:
            return
        parts = line.decode().strip().split()
        if len(parts) < 2:
            http_send(client, b"400 Bad Request", body="bad request")
            return
        method, raw_path = parts[0], parts[1]
        headers = {}
        while True:
            line = socket_readline(client)
            if not line or line == b"\r\n":
                break
            key, value = line.decode().split(":", 1)
            headers[key.lower()] = value.strip()

        path, query = parse_query(raw_path)
        content_length = int(headers.get("content-length", "0"))
        log(LOG_DEBUG, "http:", method, path, query, "len", content_length)

        if method == "GET" and path == "/":
            self.http_index(client)
        elif method == "GET" and path == "/status":
            http_json(client, b"200 OK", self.status())
        elif method == "GET" and path == "/images":
            images = [{"name": name, "size": size} for name, size in list_images()]
            http_json(client, b"200 OK", {"images": images, "free": fs_free_bytes()})
        elif method == "PUT" and path.startswith("/images/"):
            name = safe_image_name(path[len("/images/"):])
            self.upload_image(client, name, content_length)
            http_json(client, b"200 OK", self.status("uploaded %s" % name))
        elif method == "DELETE" and path.startswith("/images/"):
            name = safe_image_name(path[len("/images/"):])
            self.delete_image(name)
            http_json(client, b"200 OK", self.status("deleted %s" % name))
        elif method == "POST" and path == "/show":
            if "image" in query:
                self.pending = ("show", safe_image_name(query["image"]))
            elif query.get("color") == "white":
                self.pending = ("color", WHITE)
            elif query.get("color") == "black":
                self.pending = ("color", BLACK)
            else:
                raise ValueError("missing image or color")
            http_json(client, b"202 Accepted", self.status("queued"))
        elif method == "POST" and path == "/delete":
            name = safe_image_name(query.get("image", ""))
            self.delete_image(name)
            http_json(client, b"200 OK", self.status("deleted %s" % name))
        else:
            http_send(client, b"404 Not Found", body="not found")

    def http_index(self, client):
        # Tiny browser interface. JavaScript uses PUT so the selected .bin file
        # is sent as the request body without multipart/form-data overhead.
        items = ""
        for name, size in list_images():
            items += (
                "<li><b>%s</b> %d bytes "
                "<button onclick=\"showImage('%s')\">Show</button> "
                "<button onclick=\"deleteImage('%s')\">Delete</button></li>"
            ) % (name, size, name, name)
        body = """<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ePaper Display</title></head>
<body>
<h1>ePaper Display</h1>
<p>IP: %s<br>Free: %d bytes<br>Current: %s</p>
<input id="file" type="file" accept=".bin">
<button onclick="upload()">Upload .bin</button>
<button onclick="showColor('white')">White</button>
<button onclick="showColor('black')">Black</button>
<ul>%s</ul>
<pre id="out"></pre>
<script>
function log(t){document.getElementById('out').textContent=t}
function upload(){
  const f=document.getElementById('file').files[0]; if(!f){log('choose a file'); return}
  fetch('/images/'+encodeURIComponent(f.name),{method:'PUT',body:f}).then(r=>r.text()).then(log)
}
function showImage(n){fetch('/show?image='+encodeURIComponent(n),{method:'POST'}).then(r=>r.text()).then(log)}
function showColor(c){fetch('/show?color='+c,{method:'POST'}).then(r=>r.text()).then(log)}
function deleteImage(n){fetch('/images/'+encodeURIComponent(n),{method:'DELETE'}).then(r=>r.text()).then(log)}
</script>
</body></html>""" % (self.ip_address(), fs_free_bytes(), self.current, items)
        http_send(client, b"200 OK", b"text/html", body)

    def heartbeat(self):
        now = ticks_ms()
        if ticks_due(now, self.last_heartbeat, HEARTBEAT_INTERVAL_MS):
            self.last_heartbeat = now
            self.publish(b"heartbeat", self.status("heartbeat"))
            log(LOG_DEBUG, "heartbeat:", self.status("heartbeat"))

    def poll_mqtt(self):
        if not self.network_connected():
            self.close_mqtt()
            return
        if not self.mqtt:
            self.connect_mqtt()
            return
        try:
            self.mqtt.check_msg()
        except Exception as err:
            log(LOG_INFO, "mqtt: check failed", err)
            try:
                self.mqtt.disconnect()
            except Exception:
                pass
            self.mqtt = None

    def run(self):
        # Boot order: initialize the display, wait for network, then keep the
        # webserver, MQTT connection, pending display commands, and heartbeat
        # alive in a simple cooperative loop.
        self.epd.init()
        while not self.ensure_network():
            log(LOG_INFO, "net: waiting before app start")
            sleep_ms(500)
        self.connect_mqtt(force=True)
        self.publish_status("booted")
        while True:
            network_ok = self.ensure_network()
            if network_ok:
                self.handle_http()
                self.poll_mqtt()
            self.process_pending()
            self.heartbeat()
            sleep_ms(20)


def run_app():
    app = EpaperApp()
    app.run()


def boot():
    # When this file is copied to the Pico as main.py, MicroPython runs it on
    # boot. This delay gives you a short window to open USB serial and press
    # Ctrl-C before the network/display app starts.
    log(LOG_INFO, "boot: press Ctrl-C within", BOOT_DELAY_MS // 1000, "seconds for REPL")
    sleep_ms(BOOT_DELAY_MS)
    run_app()


if __name__ == "__main__":
    boot()
