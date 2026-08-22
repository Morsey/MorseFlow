"""
Minimal I2C scanner for the ToF PIB.

Copy this script to the device filesystem root alongside config.py, then run:

    import scan_i2c
    scan_i2c.main()
"""

from machine import I2C, Pin

import config


def _make_i2c():
    try:
        from machine import SoftI2C

        return SoftI2C(
            sda=Pin(config.TOF_SDA_PIN),
            scl=Pin(config.TOF_SCL_PIN),
            freq=config.I2C_FREQ,
        )
    except ImportError:
        return I2C(
            0,
            sda=Pin(config.TOF_SDA_PIN),
            scl=Pin(config.TOF_SCL_PIN),
            freq=config.I2C_FREQ,
        )


def main():
    print("I2C scan")
    print("SDA GPIO{} SCL GPIO{}".format(config.TOF_SDA_PIN, config.TOF_SCL_PIN))
    addresses = _make_i2c().scan()

    if not addresses:
        print("No I2C devices found")
        return

    print("Found {} device(s):".format(len(addresses)))
    for address in addresses:
        print("  0x{:02X} ({})".format(address, address))


if __name__ == "__main__":
    main()
