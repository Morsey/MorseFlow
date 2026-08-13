import micropython
from machine import Pin

from debug import log
import pins


# Keep MicroPython's default USB serial REPL active for development and recovery.
# Ctrl-C can interrupt the app loop when a USB REPL is attached.
micropython.kbd_intr(3)

log("boot", "USB serial REPL enabled; Ctrl-C interrupt is active")

boot_repl_button = Pin(pins.BOOT_REPL_BUTTON, Pin.IN, Pin.PULL_UP)
if boot_repl_button.value() == 0:
    log("boot", "boot REPL button held; app start skipped")
else:
    log("boot", "starting MorseFlow app")

    import app
    app.main()
