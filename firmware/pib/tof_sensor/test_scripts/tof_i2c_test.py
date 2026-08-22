"""
PIB ToF sensor I2C and output test.

Copy this script to the ToF PIB filesystem root alongside config.py, then run:

    import tof_i2c_test
    tof_i2c_test.main()

This verifies the local PIB-to-ToF I2C wiring and pulses the two
Morseboard-facing status outputs for visual checking.
"""

from machine import I2C, Pin
from time import sleep_ms

import config


def log(message):
    if config.DEBUG_REPL:
        print(message)


def _format_addresses(addresses):
    if not addresses:
        return "none"
    return ", ".join("0x{:02X}".format(address) for address in addresses)


def _read_u8(i2c, address, register):
    try:
        return i2c.readfrom_mem(address, register, 1)[0]
    except Exception:
        return None


def _read_u8_16bit_reg(i2c, address, register):
    try:
        return i2c.readfrom_mem(address, register, 1, addrsize=16)[0]
    except TypeError:
        high = (register >> 8) & 0xFF
        low = register & 0xFF
        try:
            i2c.writeto(address, bytes((high, low)))
            return i2c.readfrom(address, 1)[0]
        except Exception:
            return None
    except Exception:
        return None


class StatusOutputs:
    def __init__(self):
        self.near = Pin(config.STATUS_NEAR_PIN, Pin.OUT)
        self.far = Pin(config.STATUS_FAR_PIN, Pin.OUT)
        self.off()

    def off(self):
        self.near.value(0)
        self.far.value(0)

    def error(self):
        self.near.value(1)
        self.far.value(1)

    def pulse_test(self):
        log("Pulse near/status A output GPIO{}".format(config.STATUS_NEAR_PIN))
        self.near.value(1)
        sleep_ms(config.OUTPUT_PULSE_MS)
        self.near.value(0)
        sleep_ms(config.OUTPUT_PULSE_MS)

        log("Pulse far/status B output GPIO{}".format(config.STATUS_FAR_PIN))
        self.far.value(1)
        sleep_ms(config.OUTPUT_PULSE_MS)
        self.far.value(0)
        sleep_ms(config.OUTPUT_PULSE_MS)


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


def _print_identity_hints(i2c):
    address = config.TOF_ADDRESS
    l0x_model_id = _read_u8(i2c, address, 0xC0)
    l0x_revision_id = _read_u8(i2c, address, 0xC2)
    l1x_model_id = _read_u8_16bit_reg(i2c, address, 0x010F)
    l1x_module_type = _read_u8_16bit_reg(i2c, address, 0x0110)

    log(
        "VL53L0X ID hints: model=0x{} revision=0x{}".format(
            "--" if l0x_model_id is None else "{:02X}".format(l0x_model_id),
            "--" if l0x_revision_id is None else "{:02X}".format(l0x_revision_id),
        )
    )
    log(
        "VL53L1X ID hints: model=0x{} module=0x{}".format(
            "--" if l1x_model_id is None else "{:02X}".format(l1x_model_id),
            "--" if l1x_module_type is None else "{:02X}".format(l1x_module_type),
        )
    )


def main(repeat=True):
    log("PIB ToF I2C test")
    log("SDA GPIO{} SCL GPIO{}".format(config.TOF_SDA_PIN, config.TOF_SCL_PIN))
    log("Expected ToF I2C address: 0x{:02X}".format(config.TOF_ADDRESS))

    power = None
    if config.POWER_ENABLE_PIN is not None:
        power = Pin(config.POWER_ENABLE_PIN, Pin.OUT)
        power.value(1)
        log("Local sensor power enabled on GPIO{}".format(config.POWER_ENABLE_PIN))
        sleep_ms(config.POWER_SETTLE_MS)

    outputs = StatusOutputs()
    i2c = _make_i2c()

    try:
        while True:
            outputs.pulse_test()
            addresses = i2c.scan()
            log("I2C devices: {}".format(_format_addresses(addresses)))

            if config.TOF_ADDRESS in addresses:
                outputs.far.value(1)
                outputs.near.value(0)
                log("ToF sensor responded at 0x{:02X}".format(config.TOF_ADDRESS))
                _print_identity_hints(i2c)
            else:
                outputs.error()
                log("No ToF sensor found")

            if not repeat:
                break
            sleep_ms(config.SCAN_INTERVAL_MS)
    finally:
        outputs.off()
        if power is not None:
            power.value(0)
            log("Local sensor power disabled")
        log("PIB ToF I2C test stopped")


if __name__ == "__main__":
    main()
