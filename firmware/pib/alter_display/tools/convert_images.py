#!/usr/bin/env python3
from pathlib import Path
import subprocess

try:
    from PIL import Image
except ImportError:
    Image = None


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "images"
WIDTH = 128
HEIGHT = 64
PORTRAIT_WIDTH = 64
PORTRAIT_HEIGHT = 128
THRESHOLD = 128


def pixels_from_pillow(path):
    image = Image.open(path).convert("L")
    image.thumbnail((PORTRAIT_WIDTH, PORTRAIT_HEIGHT))

    canvas = Image.new("L", (PORTRAIT_WIDTH, PORTRAIT_HEIGHT), 0)
    x = (PORTRAIT_WIDTH - image.width) // 2
    y = (PORTRAIT_HEIGHT - image.height) // 2
    canvas.paste(image, (x, y))
    canvas = canvas.transpose(Image.Transpose.ROTATE_270)
    return canvas.tobytes()


def pixels_from_imagemagick(path):
    command = [
        "magick", str(path),
        "-colorspace", "Gray",
        "-resize", "{}x{}".format(PORTRAIT_WIDTH, PORTRAIT_HEIGHT),
        "-gravity", "center",
        "-background", "black",
        "-extent", "{}x{}".format(PORTRAIT_WIDTH, PORTRAIT_HEIGHT),
        "-rotate", "90",
        "-depth", "8",
        "gray:-",
    ]
    return subprocess.run(command, check=True, capture_output=True).stdout


def convert_image(path):
    if Image is not None:
        pixels = pixels_from_pillow(path)
    else:
        pixels = pixels_from_imagemagick(path)

    expected = WIDTH * HEIGHT
    if len(pixels) != expected:
        raise ValueError(
            "expected {} grayscale pixels from {}, got {}".format(
                expected, path.name, len(pixels)
            )
        )

    output = bytearray(WIDTH * HEIGHT // 8)
    for yy in range(HEIGHT):
        for xx in range(WIDTH):
            if pixels[yy * WIDTH + xx] > THRESHOLD:
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
