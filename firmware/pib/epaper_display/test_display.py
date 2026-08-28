import config
from display_controller import image_path, list_images
from epaper_display import EPD7in3F


def _read_choice(prompt):
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        raise
    except Exception:
        # Some MicroPython REPLs can raise EOF-style errors on disconnect.
        return ""


def main():
    print("E-paper display PIB test")
    print("SPI{} SCK GPIO{} MOSI GPIO{}".format(
        config.SPI_BUS,
        config.EPD_SCK_PIN,
        config.EPD_MOSI_PIN,
    ))
    print("CS GPIO{} DC GPIO{} RST GPIO{} BUSY GPIO{}".format(
        config.EPD_CS_PIN,
        config.EPD_DC_PIN,
        config.EPD_RST_PIN,
        config.EPD_BUSY_PIN,
    ))

    epd = EPD7in3F()
    epd.init()

    try:
        while True:
            image = _choose_image()
            if image is None:
                continue
            print("Displaying image: {}".format(image))
            epd.display_file(image_path(image))
    except KeyboardInterrupt:
        print("")
        print("Stopping display test")
    finally:
        epd.sleep()
        print("Display sleeping")


def _choose_image():
    images = list_images()
    if not images:
        print("No .bin images found in {} or root.".format(config.IMAGE_DIR))
        _read_choice("Upload images, then press Enter to rescan. Ctrl-C to stop: ")
        return None

    print("")
    print("Available .bin images:")
    for index, item in enumerate(images, 1):
        print("{}: {} ({} bytes)".format(index, item["name"], item["size"]))

    choice = _read_choice("Select image number/name, r=rescan, Ctrl-C=stop: ")
    if choice.lower() in ("", "r", "rescan"):
        return None

    try:
        index = int(choice)
        if 1 <= index <= len(images):
            return images[index - 1]["name"]
    except ValueError:
        pass

    for item in images:
        if item["name"] == choice:
            return item["name"]

    if not choice.endswith(".bin"):
        choice += ".bin"
    for item in images:
        if item["name"] == choice:
            return item["name"]

    print("Unknown image: {}".format(choice))
    return None


if __name__ == "__main__":
    main()
