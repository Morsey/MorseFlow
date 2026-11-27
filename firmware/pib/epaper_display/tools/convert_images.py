#!/usr/bin/env python3
"""Convert images to DKE 7.5-inch black/white/red two-plane buffers."""

__version__ = "1.0.0"

import argparse
from pathlib import Path

from PIL import Image, ImageOps


WIDTH = 800
HEIGHT = 480
PLANE_SIZE = WIDTH * HEIGHT // 8
BUFFER_SIZE = PLANE_SIZE * 2

SOURCE_DIR = Path(__file__).resolve().parents[1] / "images" / "source"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "images" / "bin"
DEFAULT_ROTATION = 90

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}

COLORS = ((0, 0, 0), (255, 255, 255), (255, 0, 0))


def build_palette_image():
    palette = []
    for color in COLORS:
        palette.extend(color)
    palette.extend([0, 0, 0] * (256 - len(COLORS)))

    image = Image.new("P", (1, 1))
    image.putpalette(palette)
    return image


def fit_to_display(image, rotation):
    image = ImageOps.exif_transpose(image.convert("RGB"))
    if rotation:
        image = image.rotate(rotation, expand=True)
    return ImageOps.fit(
        image,
        (WIDTH, HEIGHT),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def quantize_to_epaper_palette(image):
    palette_image = build_palette_image()
    indexed = image.quantize(palette=palette_image, dither=Image.Dither.FLOYDSTEINBERG)
    return indexed.convert("RGB")


def pack_image(image):
    if image.size != (WIDTH, HEIGHT):
        raise ValueError("image must be {}x{} pixels".format(WIDTH, HEIGHT))

    pixels = image.load()
    black = bytearray([0xFF] * PLANE_SIZE)
    red = bytearray(PLANE_SIZE)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            index = y * (WIDTH // 8) + (x // 8)
            mask = 0x80 >> (x & 7)
            color = pixels[x, y]
            if color == (0, 0, 0):
                black[index] &= ~mask
            elif color == (255, 0, 0):
                red[index] |= mask
    return black + red


def convert_image(source_path, output_path, rotation):
    with Image.open(source_path) as source:
        fitted = fit_to_display(source, rotation)
    converted = quantize_to_epaper_palette(fitted)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(pack_image(converted))
    return output_path.stat().st_size


def iter_sources(source_dir):
    for path in sorted(source_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def main():
    parser = argparse.ArgumentParser(
        description="Convert images to 800x480 black/white/red two-plane .bin files."
    )
    parser.add_argument(
        "sources",
        nargs="*",
        type=Path,
        help="Specific image file(s). Defaults to every supported file in images/source.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for generated .bin files.",
    )
    parser.add_argument(
        "--rotate",
        type=int,
        choices=(0, 90, 180, 270),
        default=DEFAULT_ROTATION,
        help="Rotate source image before fitting to the 800x480 display.",
    )
    args = parser.parse_args()

    sources = args.sources or list(iter_sources(SOURCE_DIR))
    if not sources:
        raise SystemExit("No source images found in {}".format(SOURCE_DIR))

    for source_path in sources:
        output_path = args.output_dir / (source_path.stem + ".bin")
        size = convert_image(source_path, output_path, args.rotate)
        print("Wrote {} ({} bytes)".format(output_path, size))


if __name__ == "__main__":
    main()
