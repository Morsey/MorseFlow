from machine import Pin, SPI
from time import ticks_add, ticks_diff
import network

import config
from debug import log
import pins


class EthernetService:
    def __init__(self):
        self.nic = None
        self.next_attempt_ms = 0
        self.last_error = None

    def update(self, now_ms):
        if self.is_ready():
            return True
        if self.is_connected():
            if ticks_diff(now_ms, self.next_attempt_ms) >= 0:
                self.next_attempt_ms = ticks_add(now_ms, config.RECONNECT_INTERVAL_MS)
                log("ethernet", "link active; waiting for valid IP")
            return False
        if ticks_diff(now_ms, self.next_attempt_ms) < 0:
            return False
        self.next_attempt_ms = ticks_add(now_ms, config.RECONNECT_INTERVAL_MS)
        return self.connect()

    def connect(self):
        try:
            log("ethernet", "connecting W5500")
            spi = SPI(
                0,
                2_000_000,
                mosi=Pin(pins.W5500_MOSI),
                miso=Pin(pins.W5500_MISO),
                sck=Pin(pins.W5500_SCK),
            )
            self.nic = network.WIZNET5K(
                spi,
                Pin(pins.W5500_CS),
                Pin(pins.W5500_RESET),
            )
            self.nic.active(True)
            if not config.NETWORK_DHCP:
                self.nic.ifconfig((
                    config.STATIC_IP,
                    config.STATIC_SUBNET,
                    config.STATIC_GATEWAY,
                    config.STATIC_DNS,
                ))
            self.last_error = None
            if self.is_ready():
                log("ethernet", "connected with IP {}".format(self.ip_address()))
            else:
                log("ethernet", "interface active; waiting for valid IP")
            return self.is_ready()
        except Exception as exc:
            self.last_error = repr(exc)
            log("ethernet", "connect failed: {}".format(self.last_error))
            return False

    def is_connected(self):
        try:
            return self.nic is not None and self.nic.isconnected()
        except Exception:
            return False

    def is_ready(self):
        ip_address = self.ip_address()
        return self.is_connected() and ip_address not in (None, "0.0.0.0")

    def ip_address(self):
        if self.nic is None:
            return None
        try:
            return self.nic.ifconfig()[0]
        except Exception:
            return None
