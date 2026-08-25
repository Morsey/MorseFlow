import micropython

from debug import log


micropython.kbd_intr(3)
log("boot", "USB serial REPL enabled; Ctrl-C interrupt is active")
log("boot", "starting epaper display PIB app")

import app
app.main()
