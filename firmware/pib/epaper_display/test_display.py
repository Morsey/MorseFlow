__version__ = "1.0.0"

from time import sleep_ms

import versions

def main():
    if not versions.report(versions.DISPLAY):
        return
    import config
    from display_controller import image_path, list_images
    from epaper_display import EPD7in5B, WHITE, stream_test_pattern
    print("E-paper display PIB test")
    print("{} SPI SCK GPIO{} MOSI GPIO{}".format(
        "Software" if config.SPI_SOFTWARE else "Hardware SPI{}".format(config.SPI_BUS),
        config.EPD_SCK_PIN,
        config.EPD_MOSI_PIN,
    ))
    print("CS GPIO{} DC GPIO{} RST GPIO{} BUSY GPIO{}".format(
        config.EPD_CS_PIN,
        config.EPD_DC_PIN,
        config.EPD_RST_PIN,
        config.EPD_BUSY_PIN,
    ))
    print("Waveshare Rev 2.3 PWR GPIO{}".format(config.EPD_PWR_PIN))
    print("Power will be enabled before display reset")

    epd = EPD7in5B()
    initialized = False

    try:
        print("BUSY with HAT power off: {}".format(epd.busy.value()))
        epd.init()
        initialized = True
        print("BUSY after init: {} (expected idle=1)".format(epd.busy.value()))
        print("Clearing display to white")
        epd.clear(WHITE)
        sleep_ms(config.DISPLAY_HOLD_MS)

        print("Displaying black/white/red test pattern")
        stream_test_pattern(epd)
        sleep_ms(config.DISPLAY_HOLD_MS)

        images = list_images()
        if not images:
            print("No .bin image found; skipping image step")
        else:
            image = images[0]["name"]
            print("Displaying image: {}".format(image))
            epd.display_file(image_path(image))
    except KeyboardInterrupt:
        print("")
        print("Stopping display test")
    finally:
        if initialized:
            epd.sleep()
            print("Display sleeping; PWR GPIO is low")
        else:
            epd.power_off()
            print("Display power off")


if __name__ == "__main__":
    main()
