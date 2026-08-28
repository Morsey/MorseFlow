from machine import Pin
from time import ticks_add, ticks_diff


class OnboardLED:
    def __init__(self):
        self.pin = self._make_pin()
        self.state = 0
        self.next_toggle_ms = 0
        if self.pin:
            self.pin.value(0)

    def _make_pin(self):
        for led_id in ("LED", 25, "GPIO25", "WL_GPIO0"):
            try:
                return Pin(led_id, Pin.OUT)
            except Exception:
                pass
        return None

    def off(self):
        self.state = 0
        if self.pin:
            self.pin.value(0)

    def update(self, now_ms, toggle_interval_ms):
        if not self.pin:
            return
        if ticks_diff(now_ms, self.next_toggle_ms) < 0:
            return
        self.state = 0 if self.state else 1
        self.pin.value(self.state)
        self.next_toggle_ms = ticks_add(now_ms, toggle_interval_ms)
