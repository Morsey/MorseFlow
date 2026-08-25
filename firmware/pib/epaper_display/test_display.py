import config
from epaper_display import EPD7in3F


NON_SCARE_IMAGE = "E ink Non Scare.bin"
SCARE_IMAGE = "E ink Scare.bin"


def _wait_for_key(prompt):
    try:
        input(prompt)
    except KeyboardInterrupt:
        raise
    except Exception:
        # Some MicroPython REPLs can raise EOF-style errors on disconnect.
        pass


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

    images = (
        ("non-scare", NON_SCARE_IMAGE),
        ("scare", SCARE_IMAGE),
    )
    index = 0

    try:
        while True:
            label, path = images[index]
            print("Displaying {} image: {}".format(label, path))
            epd.display_file(path)
            index = 1 - index
            _wait_for_key("Press Enter to show {} image, Ctrl-C to stop: ".format(
                images[index][0]
            ))
    except KeyboardInterrupt:
        print("")
        print("Stopping display test")
    finally:
        epd.sleep()
        print("Display sleeping")


if __name__ == "__main__":
    main()
