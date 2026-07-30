from machine import Pin
from time import ticks_add, ticks_diff

import config
import pins
from dfplayer import DFPlayer


class PropPort:
    def __init__(self, port_number, signal_a_pin, signal_b_pin, initial_high=False):
        self.port_number = port_number
        self.a = Pin(signal_a_pin, Pin.OUT)
        self.b = Pin(signal_b_pin, Pin.OUT)
        self.a_deadline = None
        self.b_deadline = None
        initial = 1 if initial_high else 0
        self.a.value(initial)
        self.b.value(initial)

    def set_a(self, enabled):
        self.a_deadline = None
        self.a.value(1 if enabled else 0)

    def set_b(self, enabled):
        self.b_deadline = None
        self.b.value(1 if enabled else 0)

    def pulse_a(self, now_ms, duration_ms):
        self.a.value(1)
        self.a_deadline = ticks_add(now_ms, max(0, int(duration_ms)))

    def pulse_b(self, now_ms, duration_ms):
        self.b.value(1)
        self.b_deadline = ticks_add(now_ms, max(0, int(duration_ms)))

    def update(self, now_ms):
        changed = False
        if self.a_deadline is not None and ticks_diff(now_ms, self.a_deadline) >= 0:
            self.a.value(0)
            self.a_deadline = None
            changed = True
        if self.b_deadline is not None and ticks_diff(now_ms, self.b_deadline) >= 0:
            self.b.value(0)
            self.b_deadline = None
            changed = True
        return changed

    def state(self):
        return {
            "a": bool(self.a.value()),
            "b": bool(self.b.value()),
            "a_pulse_active": self.a_deadline is not None,
            "b_pulse_active": self.b_deadline is not None,
        }


class MorseboardHardware:
    def __init__(self):
        self.power_5v = Pin(pins.PROP_POWER_ENABLE, Pin.OUT)
        self.relay = Pin(pins.OPTIONAL_RELAY, Pin.OUT)
        self.dfplayer = DFPlayer()
        self.ports = []
        self.dirty = True

        self.power_5v.value(1 if config.PROP_5V_ENABLED_AT_BOOT else 0)
        self.relay.value(1 if config.RELAY_ENABLED_AT_BOOT else 0)

        for index, pair in enumerate(pins.PORT_PINS):
            self.ports.append(
                PropPort(
                    index + 1,
                    pair[0],
                    pair[1],
                    initial_high=config.PORT_SIGNALS_HIGH_AT_BOOT,
                )
            )

    def set_power(self, enabled):
        self.power_5v.value(1 if enabled else 0)
        self.dirty = True

    def set_relay(self, enabled):
        self.relay.value(1 if enabled else 0)
        self.dirty = True

    def command_port(self, port_number, command, now_ms):
        port = self.ports[int(port_number) - 1]
        self._apply_signal_command(port, "a", command.get("a"), now_ms)
        self._apply_signal_command(port, "b", command.get("b"), now_ms)
        self.dirty = True

    def command_audio(self, command):
        if "volume" in command:
            self.dfplayer.set_volume(command["volume"])
        if "play_track" in command:
            self.dfplayer.play_track(command["play_track"])
        if command.get("stop"):
            self.dfplayer.stop()

    def update(self, now_ms):
        changed = False
        for port in self.ports:
            if port.update(now_ms):
                changed = True
        if changed:
            self.dirty = True
        return changed

    def consume_dirty(self):
        was_dirty = self.dirty
        self.dirty = False
        return was_dirty

    def state(self):
        return {
            "prop_5v_enabled": bool(self.power_5v.value()),
            "relay_enabled": bool(self.relay.value()),
            "ports": {
                str(port.port_number): port.state()
                for port in self.ports
            },
        }

    def safe_defaults(self):
        self.set_power(False)
        self.set_relay(False)
        for port in self.ports:
            port.set_a(False)
            port.set_b(False)
        self.dirty = True

    def _apply_signal_command(self, port, signal_name, value, now_ms):
        if value is None:
            return
        if isinstance(value, dict):
            pulse_ms = value.get("pulse_ms")
            if pulse_ms is not None:
                if signal_name == "a":
                    port.pulse_a(now_ms, pulse_ms)
                else:
                    port.pulse_b(now_ms, pulse_ms)
            return
        if signal_name == "a":
            port.set_a(bool(value))
        else:
            port.set_b(bool(value))

