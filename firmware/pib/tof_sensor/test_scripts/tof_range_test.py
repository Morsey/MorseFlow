"""
VL53L0X range test for the ToF PIB.

Copy this script to the PIB filesystem root alongside config.py and a
MicroPython VL53L0X driver named vl53l0x.py, then run:

    import tof_range_test
    tof_range_test.main()

The script prints distance in millimeters and drives the Morseboard-facing
status outputs:

    near/status A high, far/status B low: distance <= NEAR_THRESHOLD_MM
    near/status A low, far/status B high: distance > NEAR_THRESHOLD_MM
    both high: range read error
"""

from machine import I2C, Pin
from time import sleep_ms

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


class StatusOutputs:
    def __init__(self):
        self.near = Pin(config.STATUS_NEAR_PIN, Pin.OUT)
        self.far = Pin(config.STATUS_FAR_PIN, Pin.OUT)
        self.off()

    def off(self):
        self.near.value(0)
        self.far.value(0)

    def set_near(self):
        self.near.value(1)
        self.far.value(0)

    def set_far(self):
        self.near.value(0)
        self.far.value(1)

    def set_error(self):
        self.near.value(1)
        self.far.value(1)


def _load_driver():
    try:
        from vl53l0x import VL53L0X

        return VL53L0X
    except ImportError:
        print("Missing VL53L0X driver.")
        print("Upload a MicroPython VL53L0X driver as vl53l0x.py, then retry.")
        raise


def _new_sensor(driver_class, i2c):
    try:
        return driver_class(
            i2c,
            address=config.TOF_ADDRESS,
            io_timeout_ms=config.RANGE_TIMEOUT_MS,
        )
    except TypeError:
        try:
            return driver_class(i2c, config.TOF_ADDRESS)
        except TypeError:
            return driver_class(i2c)


def _read_distance_mm(sensor):
    if hasattr(sensor, "range"):
        value = sensor.range
        if callable(value):
            return value()
        return value
    if hasattr(sensor, "read_range_single_millimeters"):
        return sensor.read_range_single_millimeters()
    if hasattr(sensor, "read"):
        return sensor.read()
    if hasattr(sensor, "distance"):
        value = sensor.distance
        if callable(value):
            return value()
        return value
    raise AttributeError("VL53L0X driver has no recognized range method")


def main():
    print("VL53L0X PIB range test")
    print("SDA GPIO{} SCL GPIO{}".format(config.TOF_SDA_PIN, config.TOF_SCL_PIN))
    print("I2C address 0x{:02X}".format(config.TOF_ADDRESS))
    print("Near threshold: {} mm".format(config.NEAR_THRESHOLD_MM))
    print("Press Ctrl-C to stop.")

    power = None
    if config.POWER_ENABLE_PIN is not None:
        power = Pin(config.POWER_ENABLE_PIN, Pin.OUT)
        power.value(1)
        print("Local sensor power enabled on GPIO{}".format(config.POWER_ENABLE_PIN))
        sleep_ms(config.POWER_SETTLE_MS)

    outputs = StatusOutputs()
    try:
        driver_class = _load_driver()
        sensor = _new_sensor(driver_class, _make_i2c())

        while True:
            try:
                distance_mm = _read_distance_mm(sensor)
                if distance_mm is None or distance_mm >= 65535:
                    outputs.set_error()
                    print("range: invalid")
                elif distance_mm <= config.NEAR_THRESHOLD_MM:
                    outputs.set_near()
                    print("range: {} mm near".format(distance_mm))
                else:
                    outputs.set_far()
                    print("range: {} mm far".format(distance_mm))
            except Exception as exc:
                outputs.set_error()
                print("range read failed:", exc)

            sleep_ms(config.RANGE_INTERVAL_MS)
    finally:
        outputs.off()
        if power is not None:
            power.value(0)
            print("Local sensor power disabled")
        print("VL53L0X PIB range test stopped")


if __name__ == "__main__":
    main()
