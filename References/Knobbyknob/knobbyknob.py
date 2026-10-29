from machine import I2C, Pin
import utime

# Initialize GPIO 0-7 low, then toggle them high then low for proof.
pins_0_7 = [Pin(pin_num, Pin.OUT, value=0) for pin_num in range(8)]
for pin in pins_0_7:
    pin.value(1)
    utime.sleep_ms(250)
utime.sleep_ms(500)
for pin in pins_0_7:
    pin.value(0)
    utime.sleep_ms(250)

# Ensure GPIO 8-15 are low on start, then cycle them high then low.
pins_8_15 = [Pin(pin_num, Pin.OUT, value=0) for pin_num in range(8, 16)]
for pin in pins_8_15:
    pin.value(1)
    utime.sleep_ms(250)
utime.sleep_ms(500)
for pin in pins_8_15:
    pin.value(0)
    utime.sleep_ms(250)

# GP13 powers the AS5600.
Pin(13, Pin.OUT, value=1)

# LED blink at 1 Hz for status
led = Pin("LED", Pin.OUT)

# AS5600 I2C pins on Pico: GP14 SDA, GP15 SCL
# Use a much slower I2C clock rate for reliability.
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=10000)

AS5600_ADDR = 0x36
ANG_MSB_REG = 0x0C
ANG_LSB_REG = 0x0D


def read_angle_raw():
    data = i2c.readfrom_mem(AS5600_ADDR, ANG_MSB_REG, 2)
    if len(data) != 2:
        raise OSError("AS5600 read error")
    raw = (data[0] << 8) | data[1]
    return raw & 0x0FFF


def angle_degrees():
    return (read_angle_raw() * 360.0) / 4096.0


def angle_bar(angle_deg, width=60):
    filled = int((angle_deg / 360.0) * width)
    if filled < 0:
        filled = 0
    elif filled > width:
        filled = width
    bar = "#" * filled + "-" * (width - filled)
    return "[{}]".format(bar)


def is_close(angle_deg, target_deg, tol=10.0):
    d = abs((angle_deg - target_deg + 180.0) % 360.0 - 180.0)
    return d <= tol


# Relay pin (GPIO 22)
relay = Pin(22, Pin.OUT, value=0)

# Puzzle targets: 0, 180, 90, 180, 270
targets = [0.0, 180.0, 90.0, 180.0, 270.0]
current_target_idx = 0
last_hit = False

print("Starting AS5600 puzzle game...")

# detect sensor presence
devices = i2c.scan()
print("I2C devices:", [hex(x) for x in devices])
if AS5600_ADDR not in devices:
    print("Warning: AS5600 not found at 0x36. Check wiring.")

def reset_puzzle():
    global current_target_idx, last_hit
    current_target_idx = 0
    last_hit = False
    print("Puzzle reset. Start at 0°.")

try:
    while True:
        led.toggle()
        angle = angle_degrees()

        if current_target_idx < len(targets):
            target_angle = targets[current_target_idx]
            hit = is_close(angle, target_angle, tol=10.0)

            if hit and not last_hit:
                current_target_idx += 1
                print("Target {}/{} reached: {}° - Next: {}°".format(
                    current_target_idx,
                    len(targets),
                    target_angle,
                    targets[current_target_idx] if current_target_idx < len(targets) else "COMPLETE"
                ))

                if current_target_idx >= len(targets):
                    print("Puzzle complete! Activating relay for 2 seconds...")
                    relay.value(1)
                    utime.sleep_ms(2000)
                    relay.value(0)
                    print("Relay deactivated. Resetting puzzle.")
                    reset_puzzle()

            last_hit = hit
            status = "Next: {}°".format(targets[current_target_idx]) if current_target_idx < len(targets) else "SOLVED!"
        else:
            status = "SOLVED!"

        progress = "{}/{}".format(current_target_idx, len(targets))
        print("Angle: {:7.3f}° {} {} {}".format(angle, angle_bar(angle, 60), status, progress))

        utime.sleep_ms(250)
except KeyboardInterrupt:
    pass

relay.value(0)
led.off()
print("Stopped.")
