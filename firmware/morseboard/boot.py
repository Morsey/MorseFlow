import micropython
from debug import log


# Keep MicroPython's default USB serial REPL active for development and recovery.
# Ctrl-C can interrupt the app loop when a USB REPL is attached.
micropython.kbd_intr(3)

log("boot", "USB serial REPL enabled; Ctrl-C interrupt is active")
