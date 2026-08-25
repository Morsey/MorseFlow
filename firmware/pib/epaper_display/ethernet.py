from machine import Pin, SPI
from time import ticks_add, ticks_diff
import network

import config
from debug import log


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
                log("ethernet", "waiting for valid IP; ifconfig={}".format(self.ifconfig()))
            return False
        if ticks_diff(now_ms, self.next_attempt_ms) < 0:
            return False
        self.next_attempt_ms = ticks_add(now_ms, config.RECONNECT_INTERVAL_MS)
        return self.connect()

    def connect(self):
        try:
            log("ethernet", "connecting W5500")
            self.nic = self._create_interface()
            self.nic.active(True)
            if config.NETWORK_DHCP and hasattr(network, "WIZNET6K"):
                self.nic.ifconfig("dhcp")
            elif not config.NETWORK_DHCP:
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
                log("ethernet", "interface active; ifconfig={}".format(self.ifconfig()))
            return self.is_ready()
        except Exception as exc:
            self.last_error = repr(exc)
            log("ethernet", "connect failed: {}".format(self.last_error))
            return False

    def _create_interface(self):
        if hasattr(network, "WIZNET6K"):
            log("ethernet", "using network.WIZNET6K")
            return network.WIZNET6K()
        if hasattr(network, "WIZNET5K"):
            log("ethernet", "using network.WIZNET5K")
            spi = SPI(
                config.W5500_SPI_BUS,
                config.W5500_SPI_BAUDRATE,
                mosi=Pin(config.W5500_MOSI_PIN),
                miso=Pin(config.W5500_MISO_PIN),
                sck=Pin(config.W5500_SCK_PIN),
            )
            return network.WIZNET5K(
                spi,
                Pin(config.W5500_CS_PIN),
                Pin(config.W5500_RESET_PIN),
            )
        raise RuntimeError("MicroPython firmware does not include WIZnet Ethernet support")

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

    def ifconfig(self):
        if self.nic is None:
            return None
        try:
            return self.nic.ifconfig()
        except Exception as exc:
            return repr(exc)
