"""Standalone VL53L0X test on Morseboard GPIO2/GPIO3.

Copy this file and ``vl53l0x.py`` to the board filesystem root, then run:

    import vl53l0x_test
    vl53l0x_test.main()

Wiring:

    VL53L0X SDA -> GPIO2 (Port 1 Signal A)
    VL53L0X SCL -> GPIO3 (Port 1 Signal B)
    VL53L0X VIN -> switched 5V
    VL53L0X GND -> GND

The compatible driver is stored at ``firmware/pib/tof_sensor/vl53l0x.py``.
"""

from machine import I2C, Pin
from time import sleep_ms

from vl53l0x import VL53L0X


I2C_ID = 1
SDA_PIN = 2
SCL_PIN = 3
I2C_FREQUENCY = 100000
SENSOR_ADDRESS = 0x29

PROP_POWER_ENABLE_PIN = 15
POWER_SETTLE_MS = 500
READ_INTERVAL_MS = 250
RANGE_TIMEOUT_MS = 500


def main():
    power = Pin(PROP_POWER_ENABLE_PIN, Pin.OUT)
    power.value(1)

    print("VL53L0X test")
    print("SDA=GPIO{} SCL=GPIO{} I2C{}".format(SDA_PIN, SCL_PIN, I2C_ID))
    print("Switched 5V enabled on GPIO{}".format(PROP_POWER_ENABLE_PIN))
    print("Press Ctrl-C to stop.")

    try:
        sleep_ms(POWER_SETTLE_MS)
        i2c = I2C(
            I2C_ID,
            sda=Pin(SDA_PIN),
            scl=Pin(SCL_PIN),
            freq=I2C_FREQUENCY,
        )

        devices = i2c.scan()
        print("I2C devices:", ["0x{:02X}".format(address) for address in devices])
        if SENSOR_ADDRESS not in devices:
            print("VL53L0X not found at 0x29. Check power, ground, SDA, and SCL.")
            return

        sensor = VL53L0X(
            i2c,
            address=SENSOR_ADDRESS,
            io_timeout_ms=RANGE_TIMEOUT_MS,
        )
        print("VL53L0X found; reading distance.")

        while True:
            try:
                distance_mm = sensor.range
                if distance_mm >= 65535:
                    print("range: invalid")
                else:
                    print("range: {} mm".format(distance_mm))
            except Exception as exc:
                print("range read failed:", exc)

            sleep_ms(READ_INTERVAL_MS)
    finally:
        power.value(0)
        print("Switched 5V disabled; VL53L0X test stopped.")


if __name__ == "__main__":
    main()
