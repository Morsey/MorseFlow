"""Show OLED-0.bin through OLED-9.bin on one Alter Display OLED."""

from machine import Pin, SPI
from time import sleep_ms


WIDTH = 128
HEIGHT = 64

SPI_BUS = 1
SPI_BAUDRATE = 4_000_000
SCK_PIN = 10
MOSI_PIN = 11
DC_PIN = 12
RESET_PIN = 15
CS_PIN = 2

IMAGE_HOLD_MS = 2_000
IMAGE_NAMES = tuple("OLED-{}.bin".format(number) for number in range(10))


class Oled:
    def __init__(self):
        self.spi = SPI(
            SPI_BUS,
            baudrate=SPI_BAUDRATE,
            polarity=0,
            phase=0,
            sck=Pin(SCK_PIN),
            mosi=Pin(MOSI_PIN),
        )
        self.dc = Pin(DC_PIN, Pin.OUT, value=0)
        self.reset = Pin(RESET_PIN, Pin.OUT, value=1)
        self.cs = Pin(CS_PIN, Pin.OUT, value=1)
        self.buffer = bytearray(WIDTH * HEIGHT // 8)

    def command(self, value):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytes((value,)))
        self.cs.value(1)

    def data(self, values):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(values)
        self.cs.value(1)

    def initialise(self):
        self.reset.value(1)
        sleep_ms(10)
        self.reset.value(0)
        sleep_ms(50)
        self.reset.value(1)
        sleep_ms(100)

        commands = (
            0xAE, 0xD5, 0x80, 0xA8, 0x3F, 0xD3, 0x00, 0x40,
            0xA1, 0xC8, 0xDA, 0x12, 0x81, 0xFF, 0xD9, 0x22,
            # Page addressing matches the page-by-page writes in show().
            0xDB, 0x35, 0xA4, 0xA6, 0x20, 0x02, 0xAF,
        )
        for value in commands:
            self.command(value)

    def load_image(self, name):
        with open(name, "rb") as image_file:
            image = image_file.read()

        expected_size = len(self.buffer)
        if len(image) != expected_size:
            raise ValueError(
                "{} must be {} bytes; got {}".format(
                    name, expected_size, len(image)
                )
            )
        self.buffer[:] = image

    def show(self):
        for page in range(HEIGHT // 8):
            self.command(0xB0 + page)
            self.command(0x00)
            self.command(0x10)
            start = page * WIDTH
            self.data(self.buffer[start:start + WIDTH])


def main():
    print("Starting Alter Display OLED test on CS GPIO{}".format(CS_PIN))
    oled = Oled()
    oled.initialise()

    while True:
        for name in IMAGE_NAMES:
            print("Displaying {}".format(name))
            oled.load_image(name)
            oled.show()
            sleep_ms(IMAGE_HOLD_MS)


main()
