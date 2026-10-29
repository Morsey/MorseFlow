# Alter Display OLED Test

This is a standalone MicroPython test for display 1 of the Alter Display PIB.
It continuously displays `OLED-0.bin` through `OLED-9.bin`, holding each image
for two seconds.

Copy `main.py` and all ten `.bin` files to the root of a Raspberry Pi Pico,
then reset the Pico. Naming the script `main.py` makes it start automatically
on boot. Each image must be exactly 1024 bytes in the OLED's page-packed 128x64
format. The Alter Display image converter rotates the portrait JPG sources into
this display-ready layout.

Wiring used by the script:

| OLED pin | Pico GPIO |
| --- | --- |
| SCK | GPIO10 |
| SDA / MOSI | GPIO11 |
| DC | GPIO12 |
| RES | GPIO15 |
| CS | GPIO2 |
| GND | GND |
| VCC | 3V3 |

The display is configured as a 128x64 SSD1309-compatible SPI OLED at 4 MHz.
