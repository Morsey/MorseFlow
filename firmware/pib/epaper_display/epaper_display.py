from machine import Pin, SPI
from time import sleep_ms, ticks_diff, ticks_ms

import config


BLACK = 0x0
WHITE = 0x1
GREEN = 0x2
BLUE = 0x3
RED = 0x4
YELLOW = 0x5
ORANGE = 0x6

WIDTH = config.EPD_WIDTH
HEIGHT = config.EPD_HEIGHT
BUFFER_SIZE = WIDTH * HEIGHT // 2
ROW_SIZE = WIDTH // 2

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


def log(*parts):
    if config.DEBUG_REPL:
        print(*parts)


def pack_color(color):
    return (color << 4) | color


def _make_spi():
    spi = SPI(
        config.SPI_BUS,
        baudrate=config.SPI_BAUDRATE,
        sck=Pin(config.EPD_SCK_PIN),
        mosi=Pin(config.EPD_MOSI_PIN),
    )
    cs = Pin(config.EPD_CS_PIN, Pin.OUT, value=1)
    dc = Pin(config.EPD_DC_PIN, Pin.OUT, value=0)
    rst = Pin(config.EPD_RST_PIN, Pin.OUT, value=1)
    busy = Pin(config.EPD_BUSY_PIN, Pin.IN, Pin.PULL_UP)
    return spi, cs, dc, rst, busy


def _pulse_reset(rst):
    rst(1)
    sleep_ms(20)
    rst(0)
    sleep_ms(2)
    rst(1)
    sleep_ms(20)


class EPD7in3F:
    def __init__(self):
        self.spi, self.cs, self.dc, self.rst, self.busy = _make_spi()

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

    def wait_until_idle(self, timeout_ms=None):
        if timeout_ms is None:
            timeout_ms = config.BUSY_TIMEOUT_MS
        start = ticks_ms()
        while self.busy.value() == 0:
            if ticks_diff(ticks_ms(), start) > timeout_ms:
                raise RuntimeError("e-paper busy timeout")
            sleep_ms(5)
        return ticks_diff(ticks_ms(), start)

    def init(self):
        log("epaper: init")
        _pulse_reset(self.rst)
        self.wait_until_idle()
        sleep_ms(30)

        self.command(0xAA)
        for value in (0x49, 0x55, 0x20, 0x08, 0x09, 0x18):
            self.data(value)

        self.command(0x01)
        for value in (0x3F, 0x00, 0x32, 0x2A, 0x0E, 0x2A):
            self.data(value)

        self.command(0x00)
        self.data(0x5F)
        self.data(0x69)

        self.command(0x03)
        for value in (0x00, 0x54, 0x00, 0x44):
            self.data(value)

        self.command(0x05)
        for value in (0x40, 0x1F, 0x1F, 0x2C):
            self.data(value)

        self.command(0x06)
        for value in (0x6F, 0x1F, 0x1F, 0x22):
            self.data(value)

        self.command(0x08)
        for value in (0x6F, 0x1F, 0x1F, 0x22):
            self.data(value)

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
        for value in (0x03, 0x20, 0x01, 0xE0):
            self.data(value)
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
        log("epaper: ready")

    def refresh(self):
        self.command(0x04)
        log("epaper: power on", self.wait_until_idle(), "ms")
        self.command(0x12)
        self.data(0x00)
        log("epaper: refresh", self.wait_until_idle(), "ms")
        self.command(0x02)
        self.data(0x00)
        log("epaper: power off", self.wait_until_idle(), "ms")

    def clear(self, color=WHITE):
        self.command(0x10)
        self.data_repeat(pack_color(color), BUFFER_SIZE)
        self.refresh()

    def display_file(self, path, chunk_size=1024):
        with open(path, "rb") as file:
            file.seek(0, 2)
            size = file.tell()
        if size != BUFFER_SIZE:
            raise ValueError("image file must be {} bytes".format(BUFFER_SIZE))

        chunk = bytearray(chunk_size)
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
                        self.spi.write(memoryview(chunk)[:count])
        finally:
            self.cs(1)
        self.refresh()

    def sleep(self):
        self.command(0x07)
        self.data(0xA5)
        sleep_ms(2000)


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


def stream_color_bars(epd):
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


def stream_text(epd, line1="EPAPER", line2="READY"):
    line1 = line1.upper()
    line2 = line2.upper()
    line1_scale = fit_text_scale(line1, WIDTH - 160, 10)
    line2_scale = fit_text_scale(line2, WIDTH - 260, 8)
    line1_x = (WIDTH - text_width(line1, line1_scale)) // 2
    line2_x = (WIDTH - text_width(line2, line2_scale)) // 2
    row = bytearray(ROW_SIZE)

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
        draw_text_row(row, line1, line1_x, 140, line1_scale, BLACK, y)
        draw_text_row(row, line2, line2_x, 275, line2_scale, RED, y)
        epd.spi.write(row)
    epd.cs(1)
    epd.refresh()
