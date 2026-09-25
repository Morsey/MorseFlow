"""Boot wrapper for the e-paper display app.

Upload this file as main.py alongside ePaperDIsplay.py on the Pico. MicroPython
runs main.py on boot, and this wrapper keeps the main application source in its
own file.
"""

import ePaperDIsplay


ePaperDIsplay.boot()
