from machine import Pin
from time import ticks_add, ticks_diff

import config
from debug import log
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
        log("port{}".format(self.port_number), "signal A set {}".format(int(bool(enabled))))

    def set_b(self, enabled):
        self.b_deadline = None
        self.b.value(1 if enabled else 0)
        log("port{}".format(self.port_number), "signal B set {}".format(int(bool(enabled))))

    def pulse_a(self, now_ms, duration_ms):
        self.a.value(1)
        self.a_deadline = ticks_add(now_ms, max(0, int(duration_ms)))
        log("port{}".format(self.port_number), "signal A pulse {} ms".format(duration_ms))

    def pulse_b(self, now_ms, duration_ms):
        self.b.value(1)
        self.b_deadline = ticks_add(now_ms, max(0, int(duration_ms)))
        log("port{}".format(self.port_number), "signal B pulse {} ms".format(duration_ms))

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
            "mode": "output",
            "a": bool(self.a.value()),
            "b": bool(self.b.value()),
            "a_pulse_active": self.a_deadline is not None,
            "b_pulse_active": self.b_deadline is not None,
        }


class RFIDInputPort:
    def __init__(self, port_number, signal_a_pin, signal_b_pin, metadata=None):
        self.port_number = port_number
        self.metadata = metadata or {}
        # The RFID PIB actively drives these lines high/low.
        self.signal_a = Pin(signal_a_pin, Pin.IN)
        self.signal_b = Pin(signal_b_pin, Pin.IN)
        self.correct_signal = self.metadata.get("correct_signal", "a")
        self.wrong_signal = self.metadata.get("wrong_signal", "b")
        self.last_state = None
        self.current_state = self._read_state()
        self.last_state = self.current_state
        log(
            "port{}".format(self.port_number),
            "RFID input initialized state {}".format(self.current_state),
        )

    def update(self, now_ms):
        state = self._read_state()
        if state == self.current_state:
            return False
        self.last_state = self.current_state
        self.current_state = state
        log("port{}".format(self.port_number), "RFID state {}".format(state))
        return True

    def state(self):
        return {
            "mode": "rfid_input",
            "a": bool(self.signal_a.value()),
            "b": bool(self.signal_b.value()),
            "rfid": self.current_state,
            "prop": self.metadata.get("prop"),
            "reader": self.metadata.get("reader"),
            "correct_signal": self.correct_signal,
            "wrong_signal": self.wrong_signal,
        }

    def reader_status(self):
        data = {
            "port": self.port_number,
            "rfid": self.current_state,
        }
        prop = self.metadata.get("prop")
        reader = self.metadata.get("reader")
        if prop is not None:
            data["prop"] = prop
        if reader is not None:
            data["reader"] = reader
        return data

    def event(self):
        data = {
            "port": self.port_number,
            "rfid": self.current_state,
            "previous": self.last_state,
        }
        prop = self.metadata.get("prop")
        reader = self.metadata.get("reader")
        if prop is not None:
            data["prop"] = prop
        if reader is not None:
            data["reader"] = reader
        return data

    def safe_defaults(self):
        # Input ports are never driven by the Morseboard.
        pass

    def command(self, command, now_ms):
        log(
            "port{}".format(self.port_number),
            "ignored command for RFID input {}".format(command),
        )

    def _read_state(self):
        signal_a = bool(self.signal_a.value())
        signal_b = bool(self.signal_b.value())
        correct = signal_a if self.correct_signal == "a" else signal_b
        wrong = signal_a if self.wrong_signal == "a" else signal_b
        if correct and not wrong:
            return "correct"
        if wrong and not correct:
            return "wrong"
        if correct and wrong:
            return "invalid"
        return "no_card"


class MorseboardHardware:
    def __init__(self):
        self.power_5v = Pin(pins.PROP_POWER_ENABLE, Pin.OUT)
        self.relay = Pin(pins.OPTIONAL_RELAY, Pin.OUT)
        self.dfplayer = DFPlayer()
        self.ports = []
        self.events = []
        self.dirty = True

        self.power_5v.value(1 if config.PROP_5V_ENABLED_AT_BOOT else 0)
        self.relay.value(1 if config.RELAY_ENABLED_AT_BOOT else 0)

        for index, pair in enumerate(pins.PORT_PINS):
            port_number = index + 1
            rfid_metadata = config.RFID_INPUT_PORTS.get(port_number)
            if rfid_metadata is not None:
                self.ports.append(
                    RFIDInputPort(
                        port_number,
                        pair[0],
                        pair[1],
                        metadata=rfid_metadata,
                    )
                )
            else:
                self.ports.append(
                    PropPort(
                        port_number,
                        pair[0],
                        pair[1],
                        initial_high=config.PORT_SIGNALS_HIGH_AT_BOOT,
                    )
                )

    def _is_rfid_input(self, port):
        return isinstance(port, RFIDInputPort)

    def set_power(self, enabled):
        self.power_5v.value(1 if enabled else 0)
        self.dirty = True
        log("hardware", "switched 5V set {}".format(int(bool(enabled))))

    def set_relay(self, enabled):
        self.relay.value(1 if enabled else 0)
        self.dirty = True
        log("hardware", "relay set {}".format(int(bool(enabled))))

    def command_port(self, port_number, command, now_ms):
        port = self.ports[int(port_number) - 1]
        if self._is_rfid_input(port):
            port.command(command, now_ms)
            return
        self._apply_signal_command(port, "a", command.get("a"), now_ms)
        self._apply_signal_command(port, "b", command.get("b"), now_ms)
        self.dirty = True

    def command_audio(self, command):
        log("audio", "command {}".format(command))
        if "volume" in command:
            self.dfplayer.set_volume(command["volume"])
        if "play_track" in command:
            self.dfplayer.play_track(command["play_track"])
        if command.get("stop"):
            self.dfplayer.stop()

    def update(self, now_ms):
        changed = False
        changed_rfid_ports = []
        for port in self.ports:
            if port.update(now_ms):
                changed = True
                if self._is_rfid_input(port):
                    changed_rfid_ports.append(port)
        for port in changed_rfid_ports:
            event = port.event()
            event["readers"] = self.rfid_reader_statuses()
            event["all_correct"] = self.all_rfid_readers_correct()
            self.events.append(("rfid", event))
        if changed:
            self.dirty = True
        return changed

    def rfid_reader_statuses(self):
        return [
            port.reader_status()
            for port in self.ports
            if self._is_rfid_input(port)
        ]

    def all_rfid_readers_correct(self):
        readers = self.rfid_reader_statuses()
        if not readers:
            return False
        for reader in readers:
            if reader["rfid"] != "correct":
                return False
        return True

    def consume_events(self):
        events = self.events
        self.events = []
        return events

    def consume_dirty(self):
        was_dirty = self.dirty
        self.dirty = False
        return was_dirty

    def state(self):
        rfid_readers = self.rfid_reader_statuses()
        return {
            "prop_5v_enabled": bool(self.power_5v.value()),
            "relay_enabled": bool(self.relay.value()),
            "ports": {
                str(port.port_number): port.state()
                for port in self.ports
            },
            "demon_seals": {
                "readers": rfid_readers,
                "all_correct": self.all_rfid_readers_correct(),
            },
        }

    def safe_defaults(self):
        self.set_power(config.PROP_5V_ENABLED_AT_BOOT)
        self.set_relay(False)
        for port in self.ports:
            if self._is_rfid_input(port):
                port.safe_defaults()
            else:
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
