__version__ = "1.0.0"

from machine import Pin, SPI, SoftSPI
from time import sleep_ms, ticks_diff, ticks_ms

import config


BLACK = "black"
WHITE = "white"
RED = "red"

WIDTH = config.EPD_WIDTH
HEIGHT = config.EPD_HEIGHT
PLANE_SIZE = WIDTH * HEIGHT // 8
BUFFER_SIZE = PLANE_SIZE * 2
ROW_SIZE = WIDTH // 8

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


def _make_spi():
    spi_type = SoftSPI if config.SPI_SOFTWARE else SPI
    spi_args = {
        "baudrate": config.SPI_BAUDRATE,
        "polarity": config.SPI_POLARITY,
        "phase": config.SPI_PHASE,
        "bits": 8,
        "firstbit": SPI.MSB,
        "sck": Pin(config.EPD_SCK_PIN),
        "mosi": Pin(config.EPD_MOSI_PIN),
        "miso": Pin(15),
    }
    if config.SPI_SOFTWARE:
        spi = spi_type(**spi_args)
    else:
        # Hardware SPI does not need MISO for this write-only display.
        del spi_args["miso"]
        spi = spi_type(config.SPI_BUS, **spi_args)
    cs = Pin(config.EPD_CS_PIN, Pin.OUT, value=1)
    dc = Pin(config.EPD_DC_PIN, Pin.OUT, value=0)
    rst = Pin(config.EPD_RST_PIN, Pin.OUT, value=1)
    # Waveshare configures BUSY as a plain input.  An internal pull-up can
    # overpower or interfere with the HAT's TXB0108 level-shifted output.
    busy = Pin(config.EPD_BUSY_PIN, Pin.IN)
    power = Pin(config.EPD_PWR_PIN, Pin.OUT, value=0)
    return spi, cs, dc, rst, busy, power


def _pulse_reset(rst):
    rst(1)
    sleep_ms(200)
    rst(0)
    sleep_ms(2)
    rst(1)
    sleep_ms(200)


class EPD7in5B:
    def __init__(self):
        self.spi, self.cs, self.dc, self.rst, self.busy, self.power = _make_spi()

    def power_on(self):
        self.power(1)
        sleep_ms(config.EPD_POWER_SETTLE_MS)

    def power_off(self):
        self.power(0)

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
            self.command(0x71)
            if ticks_diff(ticks_ms(), start) > timeout_ms:
                raise RuntimeError("e-paper busy timeout")
            sleep_ms(5)
        sleep_ms(200)
        return ticks_diff(ticks_ms(), start)

    def init(self):
        log("epaper: init")
        self.power_on()
        _pulse_reset(self.rst)
        # XSRUPB/FPC-8612 panels do not refresh if the normal Waveshare
        # power-setting command (0x01) is sent.  Their waveform is in OTP.
        self.command(0x00)
        self.data(0x0F)
        self.command(0x50)
        self.data(0x33)
        self.command(0x61)
        for value in (0x03, 0x20, 0x01, 0xE0):
            self.data(value)
        log("epaper: ready")

    def refresh(self):
        # This panel is powered on only after both complete planes are loaded.
        self.command(0x04)
        log("epaper: BUSY immediately after power-on command", self.busy.value())
        sleep_ms(100)
        log("epaper: power on", self.wait_until_idle(), "ms")
        self.command(0x12)
        start = ticks_ms()
        while self.busy.value():
            if ticks_diff(ticks_ms(), start) >= 1000:
                raise RuntimeError("refresh: no BUSY low observed on GPIO{} in 1 s".format(config.EPD_BUSY_PIN))
            sleep_ms(1)
        asserted = ticks_ms()
        while not self.busy.value():
            if ticks_diff(ticks_ms(), asserted) >= config.BUSY_TIMEOUT_MS:
                raise RuntimeError("refresh: BUSY stayed low")
            sleep_ms(1)
        log("epaper: refresh BUSY low for", ticks_diff(ticks_ms(), asserted), "ms")
        sleep_ms(200)

    def clear(self, color=WHITE):
        if color not in (WHITE, BLACK, RED):
            raise ValueError("unsupported clear color")
        black_byte = 0x00 if color == BLACK else 0xFF
        # FPC-8612 uses DDX=11, so its red plane is active-low.
        red_byte = 0x00 if color == RED else 0xFF
        self.command(0x10)
        self.data_repeat(black_byte, PLANE_SIZE)
        self.command(0x13)
        self.data_repeat(red_byte, PLANE_SIZE)
        self.refresh()

    def display_file(self, path, chunk_size=1024):
        with open(path, "rb") as file:
            file.seek(0, 2)
            size = file.tell()
        if size != BUFFER_SIZE:
            raise ValueError("image file must be {} bytes".format(BUFFER_SIZE))

        chunk = bytearray(chunk_size)
        with open(path, "rb") as file:
            for command in (0x10, 0x13):
                self.command(command)
                self.dc(1)
                self.cs(0)
                remaining = PLANE_SIZE
                try:
                    while remaining:
                        view = memoryview(chunk)[:min(chunk_size, remaining)]
                        count = file.readinto(view)
                        if not count:
                            raise OSError("short image plane")
                        if command == 0x13:
                            for index in range(count):
                                chunk[index] ^= 0xFF
                        self.spi.write(view[:count])
                        remaining -= count
                finally:
                    self.cs(1)
        self.refresh()

    def sleep(self):
        self.command(0x02)
        self.wait_until_idle()
        self.command(0x07)
        self.data(0xA5)
        sleep_ms(2000)
        self.power_off()


# Backwards-compatible name for code importing the previous driver class.
EPD7in3F = EPD7in5B


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

    bit_value = 0 if color == BLACK else 1
    for x in range(x0, x1):
        mask = 0x80 >> (x & 7)
        if bit_value:
            row[x >> 3] |= mask
        else:
            row[x >> 3] &= ~mask


def clear_row(row, color):
    packed = 0x00 if color == BLACK else 0xFF
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


def stream_test_pattern(epd):
    black_row = bytearray([0xFF] * ROW_SIZE)
    red_row = bytearray([0xFF] * ROW_SIZE)
    fill_x_range(black_row, 40, WIDTH // 3, BLACK)
    fill_x_range(red_row, WIDTH * 2 // 3, WIDTH - 40, BLACK)

    for command, row in ((0x10, black_row), (0x13, red_row)):
        epd.command(command)
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
        draw_text_row(row, line1, line1_x, 140, line1_scale, BLACK, y)
        draw_text_row(row, line2, line2_x, 275, line2_scale, BLACK, y)
        epd.spi.write(row)
    epd.cs(1)
    epd.command(0x13)
    epd.data_repeat(0xFF, PLANE_SIZE)
    epd.refresh()
