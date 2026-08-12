"""
Boot entrypoint for RFID Reader Board (RP2040-Zero).
Auto-runs MorseRFID, with a brief Ctrl-C window to stay in REPL.
"""

from utime import sleep_ms
import sys

STARTUP_GRACE_MS = 3000
STEP_MS = 100


def startup_grace_period():
    print("main.py: booting MorseRFID on Reader Board")
    print("Press Ctrl-C within 3 seconds to stay in REPL...")
    for _ in range(STARTUP_GRACE_MS // STEP_MS):
        sleep_ms(STEP_MS)


def run():
    startup_grace_period()
    __import__("MorseRFID")


try:
    run()
except KeyboardInterrupt:
    print("\nmain.py: interrupted, REPL available.")
except Exception as exc:
    print("main.py: startup failed.")
    sys.print_exception(exc)