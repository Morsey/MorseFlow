__version__ = "1.0.0"

import micropython

from debug import log


micropython.kbd_intr(3)
log("boot", "USB serial REPL enabled; Ctrl-C interrupt is active")
