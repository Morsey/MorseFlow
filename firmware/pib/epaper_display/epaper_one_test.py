from epaper_display import EPD7in5B, HEIGHT, ROW_SIZE
from time import sleep_ms, ticks_ms, ticks_diff

epd = EPD7in5B()
try:
    epd.init()
    epd.command(0x04)              # Power on before loading pixels
    sleep_ms(100)
    epd.wait_until_idle()

    epd.command(0x91)              # Enter windowed addressing
    epd.command(0x90)              # Select x=0..799, y=0..479
    epd.data(bytes((0, 0, 3, 31, 0, 0, 1, 223, 1)))

    white = b"\xff" * ROW_SIZE
    stripe = b"\xff" * 25 + b"\x00" * 50 + b"\xff" * 25
    epd.command(0x10)
    for y in range(HEIGHT):
        epd.data(stripe if 120 <= y < 360 else white)

    epd.command(0x13)
    epd.data_repeat(0xff, ROW_SIZE * HEIGHT)
    epd.command(0x92)              # Leave windowed addressing

    epd.command(0x12)              # Request one refresh
    start = ticks_ms()
    while epd.busy.value() and ticks_diff(ticks_ms(), start) < 3000:
        sleep_ms(1)

    if epd.busy.value() == 0:
        print("Refresh BUSY went low")
        epd.wait_until_idle()
        print("Refresh BUSY returned high")
    else:
        print("No refresh BUSY pulse observed in 3 seconds")
finally:
    try:
        epd.sleep()
    finally:
        epd.power_off()