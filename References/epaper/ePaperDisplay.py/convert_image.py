#!/usr/bin/env python3
"""Convert desktop image files to the raw buffer used by ePaperDIsplay.py.

This runs on a Mac with normal Python and Pillow installed. It does not run on
the Pico. The output file is 192000 bytes for the Waveshare 7.3-inch display.

https://github.com/matthewbadeau/7-Color-E-paper-Image-converter
"""

import argparse
from pathlib import Path

from PIL import Image

import color_epd_converter


WIDTH = 800
HEIGHT = 480
BUFFER_SIZE = WIDTH * HEIGHT // 2

PALETTE = {
    (0, 0, 0): 0x0,  # black
    (255, 255, 255): 0x1,  # white
    (0, 255, 0): 0x2,  # green
    (0, 0, 255): 0x3,  # blue
    (255, 0, 0): 0x4,  # red
    (255, 255, 0): 0x5,  # yellow
    (255, 128, 0): 0x6,  # orange
}


def pack_image(image):
    """Pack an 800x480 RGB image into two 4-bit pixels per byte."""
    if image.size != (WIDTH, HEIGHT):
        raise ValueError("image must be %dx%d pixels" % (WIDTH, HEIGHT))

    pixels = image.load()
    output = bytearray(BUFFER_SIZE)
    index = 0

    for y in range(HEIGHT):
        for x in range(0, WIDTH, 2):
            left = PALETTE[pixels[x, y]]
            right = PALETTE[pixels[x + 1, y]]
            output[index] = (left << 4) | right
            index += 1

    return output


def convert_to_bin(input_path, output_path):
    with Image.open(input_path) as source:
        image = source.convert("RGB")

    image = color_epd_converter.convert(
        image,
        orientation="portrait",
        width=WIDTH,
        height=HEIGHT,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pack_image(image))


def main():
    parser = argparse.ArgumentParser(
        description="Convert an image to the raw 7-color e-paper buffer."
    )
    parser.add_argument("input", type=Path, help="Source image, e.g. pictures/photo.jpg")
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        help="Output .bin path. Defaults to export/<input-name>.bin",
    )
    args = parser.parse_args()

    output = args.output
    if output is None:
        output = Path("export") / (args.input.stem + ".bin")

    convert_to_bin(args.input, output)
    print("Wrote %s (%d bytes)" % (output, output.stat().st_size))


if __name__ == "__main__":
    main()
