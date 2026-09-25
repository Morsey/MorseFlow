from machine import Pin, SPI
from time import sleep_ms, ticks_diff, ticks_ms
import os

import config


class SpiOled:
    def __init__(self, spi, dc, res, cs, width, height, controller="ssd1309"):
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        self.width = width
        self.height = height
        self.pages = height // 8
        self.controller = controller
        self.buffer = bytearray(width * self.pages)
        self.cs.init(Pin.OUT, value=1)

    def write_cmd(self, cmd):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)
        sleep_ms(1)

    def write_data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(data)
        self.cs.value(1)

    def init(self):
        cmds = [
            0xAE,
            0xD5, 0x80,
            0xA8, 0x3F,
            0xD3, 0x00,
            0x40,
            0xA1,
            0xC8,
            0xDA, 0x12,
            0x81, 0x9F,
            0xD9, 0x22,
            0xDB, 0x35,
            0xA4,
            0xA6,
            0x20, 0x00,
            0xAF,
        ]

        for cmd in cmds:
            self.write_cmd(cmd)

    def fill(self, color):
        fill_byte = 0xFF if color else 0x00
        for index in range(len(self.buffer)):
            self.buffer[index] = fill_byte

    def load_buffer(self, data):
        expected = self.width * self.pages
        if len(data) != expected:
            raise ValueError("expected {} bytes, got {}".format(expected, len(data)))
        self.buffer[:] = data

    def pixel(self, x, y, on=True):
        if 0 <= x < self.width and 0 <= y < self.height:
            index = x + (y // 8) * self.width
            bit = 1 << (y % 8)
            if on:
                self.buffer[index] |= bit
            else:
                self.buffer[index] &= ~bit

    def text(self, text, x, y, color=1):
        # Minimal 5x7 text would add noise to bring-up. Use geometric tests first.
        pass

    def rect(self, x, y, width, height, color=1):
        for xx in range(x, x + width):
            self.pixel(xx, y, color)
            self.pixel(xx, y + height - 1, color)
        for yy in range(y, y + height):
            self.pixel(x, yy, color)
            self.pixel(x + width - 1, yy, color)

    def line(self, x1, y1, x2, y2, color=1):
        if x1 == x2:
            start = min(y1, y2)
            end = max(y1, y2)
            for y in range(start, end + 1):
                self.pixel(x1, y, color)
        elif y1 == y2:
            start = min(x1, x2)
            end = max(x1, x2)
            for x in range(start, end + 1):
                self.pixel(x, y1, color)

    def show(self):
        for page in range(self.pages):
            self.write_cmd(0xB0 + page)
            self.write_cmd(0x00)
            self.write_cmd(0x10)
            start = page * self.width
            self.write_data(self.buffer[start:start + self.width])

    def poweroff(self):
        self.write_cmd(0xAE)

    def all_pixels_on(self, enabled):
        self.write_cmd(0xA5 if enabled else 0xA4)


class RotaryEncoder:
    def __init__(self, clk_pin, dt_pin, sw_pin):
        self.clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self.dt = Pin(dt_pin, Pin.IN, Pin.PULL_UP)
        self.sw = Pin(sw_pin, Pin.IN, Pin.PULL_UP)
        self.last_state = (self.clk.value() << 1) | self.dt.value()
        self.last_sw = self.sw.value()
        self.step_accumulator = 0
        self.last_edge_ms = ticks_ms()
        self.last_press_ms = ticks_ms()

    def read_turn(self):
        state = (self.clk.value() << 1) | self.dt.value()
        if state == self.last_state:
            return 0

        now = ticks_ms()
        if ticks_diff(now, self.last_edge_ms) < config.ENCODER_DEBOUNCE_MS:
            return 0
        self.last_edge_ms = now

        transition = (self.last_state << 2) | state
        self.last_state = state

        if transition in (0b1101, 0b0100, 0b0010, 0b1011):
            self.step_accumulator += 1
        elif transition in (0b1110, 0b0111, 0b0001, 0b1000):
            self.step_accumulator -= 1
        else:
            self.step_accumulator = 0
            return 0

        if self.step_accumulator >= config.ENCODER_STEPS_PER_DETENT:
            self.step_accumulator = 0
            return 1
        if self.step_accumulator <= -config.ENCODER_STEPS_PER_DETENT:
            self.step_accumulator = 0
            return -1
        return 0

    def read_press(self):
        sw = self.sw.value()
        now = ticks_ms()
        pressed = (
            self.last_sw == 1
            and sw == 0
            and ticks_diff(now, self.last_press_ms) >= config.ENCODER_BUTTON_DEBOUNCE_MS
        )
        if pressed:
            self.last_press_ms = now
        self.last_sw = sw
        return pressed


def reset_displays(res):
    res.value(1)
    sleep_ms(10)
    res.value(0)
    sleep_ms(50)
    res.value(1)
    sleep_ms(100)


def draw_test_pattern(display, index, tick):
    display.fill(0)
    display.rect(0, 0, display.width, display.height, 1)

    for x in range(8, display.width - 8, 8):
        if (x // 8) % 2 == 0:
            display.line(x, 8, x, display.height - 9)

    for y in range(12, display.height - 12, 12):
        display.line(8, y, display.width - 9, y)

    sweep_x = (tick * config.OLED_SWEEP_STEP_PIXELS + index * 17) % display.width
    display.line(sweep_x, 1, sweep_x, display.height - 2)
    display.show()


def image_path(name):
    if config.IMAGE_DIR == ".":
        return name
    return "{}/{}".format(config.IMAGE_DIR, name)


def load_image_file(name):
    with open(image_path(name), "rb") as image_file:
        return image_file.read()


def existing_image_files():
    try:
        names = os.listdir(config.IMAGE_DIR)
    except OSError:
        return []

    configured = []
    for name in config.IMAGE_FILES:
        if name in names:
            configured.append(name)

    if configured:
        return configured

    bins = [name for name in names if name.endswith(".bin")]
    bins.sort()
    return bins


def show_image_files(displays):
    names = existing_image_files()
    if not names:
        print("No .bin images found in {}".format(config.IMAGE_DIR))
        return False

    print("Showing {} .bin image file(s)".format(len(names)))
    image_index = 0
    while True:
        for display_index, display in enumerate(displays):
            name = names[(image_index + display_index) % len(names)]
            print("Display {}: {}".format(display_index + 1, name))
            display.load_buffer(load_image_file(name))
            display.show()
        image_index = (image_index + len(displays)) % len(names)
        sleep_ms(config.OLED_IMAGE_HOLD_MS)


def show_named_image(display, name):
    print("Display 1: {}".format(name))
    display.load_buffer(load_image_file(name))
    display.show()


def control_screen_1_with_encoder(display):
    names = existing_image_files()
    if not names:
        print("No .bin images found in {}".format(config.IMAGE_DIR))
        return False

    encoder = RotaryEncoder(
        config.ENCODER_CLK_PIN,
        config.ENCODER_DT_PIN,
        config.ENCODER_SW_PIN,
    )
    print("KY-040 CLK GPIO{} DT GPIO{} SW GPIO{}".format(
        config.ENCODER_CLK_PIN,
        config.ENCODER_DT_PIN,
        config.ENCODER_SW_PIN,
    ))
    print("Rotate to change number. Press knob to reset to first number.")

    image_index = 0
    show_named_image(display, names[image_index])

    while True:
        turn = encoder.read_turn()
        if turn:
            image_index = (image_index + turn) % len(names)
            show_named_image(display, names[image_index])

        if encoder.read_press():
            image_index = 0
            show_named_image(display, names[image_index])

        sleep_ms(config.ENCODER_POLL_MS)


def flash_all_pixels(displays):
    print("Command test: all pixels on")
    for display in displays:
        display.all_pixels_on(True)
    sleep_ms(1000)

    print("Data test: framebuffer blank")
    for display in displays:
        display.all_pixels_on(False)
        display.fill(0)
        display.show()
    sleep_ms(1000)

    print("Data test: framebuffer full")
    for display in displays:
        display.fill(1)
        display.show()
    sleep_ms(1000)

    print("Data test: framebuffer blank again")
    for display in displays:
        display.fill(0)
        display.show()
    sleep_ms(1000)


def main():
    print("Alter display OLED test")
    print("SPI{} SCK GPIO{} MOSI GPIO{}".format(
        config.SPI_BUS,
        config.OLED_SCK_PIN,
        config.OLED_MOSI_PIN,
    ))
    test_count = config.OLED_TEST_COUNT
    test_cs_pins = config.OLED_CS_PINS[:test_count]
    print("DC GPIO{} RES GPIO{} CS {}".format(
        config.OLED_DC_PIN,
        config.OLED_RES_PIN,
        test_cs_pins,
    ))
    print("Controller {} baudrate {}".format(
        config.OLED_CONTROLLER,
        config.SPI_BAUDRATE,
    ))

    spi = SPI(
        config.SPI_BUS,
        baudrate=config.SPI_BAUDRATE,
        polarity=0,
        phase=0,
        sck=Pin(config.OLED_SCK_PIN),
        mosi=Pin(config.OLED_MOSI_PIN),
    )
    dc = Pin(config.OLED_DC_PIN, Pin.OUT)
    res = Pin(config.OLED_RES_PIN, Pin.OUT)
    cs_pins = [Pin(pin, Pin.OUT, value=1) for pin in config.OLED_CS_PINS]
    test_cs_pins = cs_pins[:test_count]

    displays = [
        SpiOled(
            spi,
            dc,
            res,
            cs,
            config.OLED_WIDTH,
            config.OLED_HEIGHT,
            config.OLED_CONTROLLER,
        )
        for cs in test_cs_pins
    ]

    for cs in cs_pins:
        cs.value(1)
    dc.value(0)
    reset_displays(res)

    for display in displays:
        display.init()
    flash_all_pixels(displays)

    tick = 0
    try:
        if len(displays) == 1 and control_screen_1_with_encoder(displays[0]):
            return

        if show_image_files(displays):
            return

        while True:
            for index, display in enumerate(displays):
                draw_test_pattern(display, index, tick)
            tick += 1
            sleep_ms(config.OLED_FRAME_DELAY_MS)
    except KeyboardInterrupt:
        print("")
        print("Stopping alter display test")
    finally:
        for display in displays:
            display.fill(0)
            display.show()
            display.poweroff()
        print("Displays off")


if __name__ == "__main__":
    main()
