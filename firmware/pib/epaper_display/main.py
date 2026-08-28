from time import sleep_ms, ticks_diff, ticks_ms

import config
from debug import log
from onboard_led import OnboardLED


def _startup_interrupted(timeout_ms):
    led = OnboardLED()
    log(
        "main",
        "press Ctrl-C in the next {} ms to skip auto-start".format(timeout_ms),
    )
    try:
        start = ticks_ms()
        while ticks_diff(ticks_ms(), start) < timeout_ms:
            led.update(ticks_ms(), config.BOOT_LED_TOGGLE_MS)
            sleep_ms(10)
    except KeyboardInterrupt:
        led.off()
        return True
    led.off()
    return False


def _run_configured_module():
    module_name = config.AUTO_RUN_MODULE
    function_name = config.AUTO_RUN_FUNCTION
    log("main", "starting {}.{}()".format(module_name, function_name))
    module = __import__(module_name)
    getattr(module, function_name)()


if _startup_interrupted(config.BOOT_REPL_PAUSE_MS):
    log("main", "Ctrl-C received; auto-start skipped")
else:
    _run_configured_module()
