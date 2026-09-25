#!/usr/bin/env python3
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "images"
WIDTH = 128
HEIGHT = 64
THRESHOLD = 128


def convert_image(path):
    image = Image.open(path).convert("L")
    image.thumbnail((WIDTH, HEIGHT))

    canvas = Image.new("L", (WIDTH, HEIGHT), 0)
    x = (WIDTH - image.width) // 2
    y = (HEIGHT - image.height) // 2
    canvas.paste(image, (x, y))

    output = bytearray(WIDTH * HEIGHT // 8)
    for yy in range(HEIGHT):
        for xx in range(WIDTH):
            if canvas.getpixel((xx, yy)) > THRESHOLD:
                index = xx + (yy // 8) * WIDTH
                output[index] |= 1 << (yy % 8)

    out_path = path.with_suffix(".bin")
    out_path.write_bytes(output)
    print("{} -> {} ({} bytes)".format(path.name, out_path.name, len(output)))


def main():
    paths = []
    for suffix in ("*.jpg", "*.jpeg", "*.png"):
        paths.extend(IMAGE_DIR.glob(suffix))

    paths = sorted(paths)
    if not paths:
        raise SystemExit("No JPG/PNG files found in {}".format(IMAGE_DIR))

    converted = 0
    for path in paths:
        if path.stat().st_size == 0:
            print("Skipping empty file: {}".format(path.name))
            continue
        convert_image(path)
        converted += 1

    if converted == 0:
        raise SystemExit("No non-empty image files were converted")


if __name__ == "__main__":
    main()
