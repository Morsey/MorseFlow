"""Standalone AS5600 test for MB6 GPIO10/GPIO11."""

from machine import I2C, Pin
from time import sleep_ms


I2C_ID = 1
SDA_PIN = 10
SCL_PIN = 11
I2C_FREQUENCY = 10000
AS5600_ADDRESS = 0x36
ANGLE_REGISTER = 0x0C
POLL_MS = 250


def read_raw_angle(i2c):
    data = i2c.readfrom_mem(AS5600_ADDRESS, ANGLE_REGISTER, 2)
    if len(data) != 2:
        raise OSError("AS5600 returned {} bytes".format(len(data)))
    return ((data[0] << 8) | data[1]) & 0x0FFF


def main():
    i2c = I2C(
        I2C_ID,
        sda=Pin(SDA_PIN),
        scl=Pin(SCL_PIN),
        freq=I2C_FREQUENCY,
    )

    print("AS5600 test: I2C{} SDA=GPIO{} SCL=GPIO{}".format(
        I2C_ID,
        SDA_PIN,
        SCL_PIN,
    ))
    devices = i2c.scan()
    print("I2C devices:", [hex(address) for address in devices])

    if AS5600_ADDRESS not in devices:
        print("AS5600 not found at 0x36. Check power, ground, SDA, and SCL.")
        return

    print("AS5600 found. Turn the knob; press Ctrl-C to stop.")
    try:
        while True:
            raw = read_raw_angle(i2c)
            degrees = (raw * 360.0) / 4096.0
            print("raw={:4d} angle={:7.2f} degrees".format(raw, degrees))
            sleep_ms(POLL_MS)
    except KeyboardInterrupt:
        print("AS5600 test stopped")


if __name__ == "__main__":
    main()
