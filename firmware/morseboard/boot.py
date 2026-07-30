import micropython

import config
from debug import log


# Keep MicroPython's default USB serial REPL active for development and recovery.
# Do not disable dupterm or redirect the REPL to the DFPlayer UART.
micropython.kbd_intr(3)


def usb_connected():
    detect_pin = getattr(config, "USB_VBUS_DETECT_PIN", None)
    if detect_pin is None:
        log("boot", "USB detect disabled in config; assuming no USB host")
        return False

    try:
        from machine import Pin
        connected = bool(Pin(detect_pin, Pin.IN).value())
        log("boot", "USB VBUS detect GPIO{}={}".format(detect_pin, int(connected)))
        return connected
    except Exception as exc:
        # Fail toward REPL access if the board/firmware does not expose GPIO24.
        log("boot", "USB detect failed: {}; leaving REPL available".format(repr(exc)))
        return True


log("boot", "USB serial REPL enabled; Ctrl-C interrupt is active")

if usb_connected() and not config.AUTO_RUN_WITH_USB_CONNECTED:
    log("boot", "USB connected; MorseFlow app not auto-started")
    log("boot", "Run 'import app; app.main()' from the REPL to start manually")
else:
    log("boot", "USB not connected or auto-run override enabled; starting MorseFlow app")
    import app
    app.main()
