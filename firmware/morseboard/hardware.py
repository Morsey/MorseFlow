from machine import Pin
from time import ticks_add, ticks_diff, ticks_ms

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
        self.test_step = None
        self.test_deadline = None
        self.test_duration_ms = 500
        initial = 1 if initial_high else 0
        self.a.value(initial)
        self.b.value(initial)

    def set_a(self, enabled):
        self.a_deadline = None
        self._cancel_pin_test()
        self.a.value(1 if enabled else 0)
        log("port{}".format(self.port_number), "signal A set {}".format(int(bool(enabled))))

    def set_b(self, enabled):
        self.b_deadline = None
        self._cancel_pin_test()
        self.b.value(1 if enabled else 0)
        log("port{}".format(self.port_number), "signal B set {}".format(int(bool(enabled))))

    def pulse_a(self, now_ms, duration_ms):
        self._cancel_pin_test()
        self.a.value(1)
        self.a_deadline = ticks_add(now_ms, max(0, int(duration_ms)))
        log("port{}".format(self.port_number), "signal A pulse {} ms".format(duration_ms))

    def pulse_b(self, now_ms, duration_ms):
        self._cancel_pin_test()
        self.b.value(1)
        self.b_deadline = ticks_add(now_ms, max(0, int(duration_ms)))
        log("port{}".format(self.port_number), "signal B pulse {} ms".format(duration_ms))

    def start_pin_test(self, now_ms, duration_ms=500):
        self.a_deadline = None
        self.b_deadline = None
        self.test_duration_ms = max(0, int(duration_ms))
        self.test_step = "a"
        self.test_deadline = ticks_add(now_ms, self.test_duration_ms)
        self.b.value(0)
        self.a.value(1)
        log(
            "port{}".format(self.port_number),
            "pin test signal A {} ms".format(self.test_duration_ms),
        )

    def update(self, now_ms):
        changed = False
        if self.test_step is not None and ticks_diff(now_ms, self.test_deadline) >= 0:
            return self._advance_test(now_ms)
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
            "pin_test_active": self.test_step is not None,
            "pin_test_step": self.test_step,
        }

    def _advance_test(self, now_ms):
        if self.test_step == "a":
            self.a.value(0)
            self.b.value(1)
            self.test_step = "b"
            self.test_deadline = ticks_add(now_ms, self.test_duration_ms)
            log(
                "port{}".format(self.port_number),
                "pin test signal B {} ms".format(self.test_duration_ms),
            )
            return True
        self.b.value(0)
        self.test_step = None
        self.test_deadline = None
        log("port{}".format(self.port_number), "pin test complete")
        return True

    def _cancel_pin_test(self):
        self.test_step = None
        self.test_deadline = None


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


class CandlePort:
    def __init__(self, port_number, signal_a_pin, signal_b_pin, metadata=None):
        self.port_number = port_number
        self.metadata = metadata or {}
        self.candle = Pin(signal_a_pin, Pin.OUT)
        self.lit = Pin(signal_b_pin, Pin.IN)
        self.candle_deadline = None
        self.candle_is_on = False
        self.sensor_was_active = self._sensor_active()
        self.armed_for_trigger = not self.sensor_was_active
        self.candle.value(0)
        log(
            "port{}".format(self.port_number),
            "candle initialized sensor_active={} armed={}".format(
                int(self.sensor_was_active),
                int(self.armed_for_trigger),
            ),
        )

    def update(self, now_ms):
        changed = False
        sensor_active = self._sensor_active()

        if (
            getattr(config, "CANDLE_TRIGGER_ON_ACTIVE", False)
            and sensor_active
            and not self.candle_is_on
        ):
            self.armed_for_trigger = False
            self.turn_on(now_ms, config.CANDLE_ON_TIME_MS)
            changed = True
            log(
                "port{}".format(self.port_number),
                "candle sensor active",
            )
        elif sensor_active != self.sensor_was_active:
            changed = True
            if sensor_active:
                if self.armed_for_trigger:
                    self.armed_for_trigger = False
                    self.turn_on(now_ms, config.CANDLE_ON_TIME_MS)
                    log(
                        "port{}".format(self.port_number),
                        "candle sensor triggered",
                    )
            else:
                self.armed_for_trigger = True
                log(
                    "port{}".format(self.port_number),
                    "candle sensor idle; triggers enabled",
                )
        self.sensor_was_active = sensor_active

        if (
            self.candle_deadline is not None
            and ticks_diff(now_ms, self.candle_deadline) >= 0
        ):
            self.turn_off()
            changed = True

        return changed

    def turn_on(self, now_ms, duration_ms):
        self.candle.value(1)
        self.candle_deadline = ticks_add(now_ms, max(0, int(duration_ms)))
        self.candle_is_on = True

    def turn_off(self):
        self.candle.value(0)
        self.candle_deadline = None
        self.candle_is_on = False
        log("port{}".format(self.port_number), "candle off")

    def command(self, command, now_ms):
        if command.get("off"):
            self.turn_off()
            return
        if command.get("on"):
            duration_ms = command.get("duration_ms", config.CANDLE_ON_TIME_MS)
            self.turn_on(now_ms, duration_ms)

    def state(self):
        return {
            "mode": "candle",
            "a": bool(self.candle.value()),
            "b": bool(self.lit.value()),
            "candle_on": self.candle_is_on,
            "sensor_active": self._sensor_active(),
            "armed_for_trigger": self.armed_for_trigger,
            "prop": self.metadata.get("prop"),
            "candle": self.metadata.get("candle"),
        }

    def candle_status(self):
        data = {
            "port": self.port_number,
            "candle_on": self.candle_is_on,
            "sensor_active": self._sensor_active(),
        }
        prop = self.metadata.get("prop")
        candle = self.metadata.get("candle")
        if prop is not None:
            data["prop"] = prop
        if candle is not None:
            data["candle"] = candle
        return data

    def event(self):
        data = self.candle_status()
        data["armed_for_trigger"] = self.armed_for_trigger
        return data

    def safe_defaults(self):
        startup_pulse_ms = getattr(config, "CANDLE_STARTUP_PULSE_MS", 0)
        if startup_pulse_ms:
            self.turn_on(ticks_ms(), startup_pulse_ms)
        else:
            self.turn_off()

    def _sensor_active(self):
        return self.lit.value() == config.CANDLE_SENSOR_TRIGGER_VALUE


class DemonKnockerPort:
    def __init__(self, port_number, signal_a_pin, signal_b_pin, metadata=None):
        from neopixel import NeoPixel

        self.port_number = port_number
        self.metadata = metadata or {}
        self.solenoid = Pin(signal_a_pin, Pin.OUT)
        self.pixel_data = Pin(signal_b_pin, Pin.OUT)
        self.pixel_count = int(self.metadata.get("pixel_count", 1))
        self.pixel_color_order = self.metadata.get("pixel_color_order", "RGB")
        self.solenoid_active_low = bool(self.metadata.get("solenoid_active_low"))
        self.pixels = NeoPixel(self.pixel_data, self.pixel_count)
        self.solenoid_deadline = None
        self.test_step = None
        self.test_deadline = None
        self.test_duration_ms = 500
        self.pixel_color = (0, 0, 0)
        self._set_solenoid(False)
        self._write_pixel(self.pixel_color)
        log("port{}".format(self.port_number), "demon knocker initialized")

    def update(self, now_ms):
        if (
            self.solenoid_deadline is not None
            and ticks_diff(now_ms, self.solenoid_deadline) >= 0
        ):
            self._set_solenoid(False)
            self.solenoid_deadline = None
            log("port{}".format(self.port_number), "demon knocker solenoid off")
            return True
        if self.test_step is not None and ticks_diff(now_ms, self.test_deadline) >= 0:
            return self._advance_test(now_ms)
        return False

    def command(self, command, now_ms):
        if command.get("off"):
            self._set_solenoid(False)
            self.solenoid_deadline = None
            self.test_step = None
            self.test_deadline = None
            self.pixel_data.value(0)
            self.set_pixel((0, 0, 0))
            return
        if command.get("test_pins"):
            self.start_pin_test(now_ms, command.get("duration_ms", 500))
            return
        if command.get("knock"):
            default_duration_ms = getattr(config, "DEMON_KNOCKER_PULSE_MS", 120)
            self.knock(now_ms, command.get("duration_ms", default_duration_ms))
        if "knock_ms" in command:
            self.knock(now_ms, command["knock_ms"])
        if "solenoid" in command:
            self.solenoid_deadline = None
            self._set_solenoid(bool(command["solenoid"]))
        if "solenoid_ms" in command:
            self.knock(now_ms, command["solenoid_ms"])
        if "pixel" in command:
            self.set_pixel(command["pixel"])

    def knock(self, now_ms, duration_ms):
        self._set_solenoid(True)
        self.solenoid_deadline = ticks_add(now_ms, max(0, int(duration_ms)))
        log(
            "port{}".format(self.port_number),
            "demon knocker pulse {} ms".format(duration_ms),
        )

    def start_pin_test(self, now_ms, duration_ms):
        duration_ms = max(0, int(duration_ms))
        self.solenoid_deadline = None
        self.test_duration_ms = duration_ms
        self.test_step = "solenoid"
        self.test_deadline = ticks_add(now_ms, duration_ms)
        self.pixel_data.value(0)
        self._set_solenoid(True)
        log(
            "port{}".format(self.port_number),
            "pin test solenoid {} ms".format(duration_ms),
        )

    def _advance_test(self, now_ms):
        if self.test_step == "solenoid":
            self._set_solenoid(False)
            self.pixel_data.value(1)
            self.test_step = "pixel_data"
            self.test_deadline = ticks_add(now_ms, self.test_duration_ms)
            log(
                "port{}".format(self.port_number),
                "pin test pixel data {} ms".format(self.test_duration_ms),
            )
            return True
        self.pixel_data.value(0)
        self.test_step = None
        self.test_deadline = None
        self._write_pixel(self.pixel_color)
        log("port{}".format(self.port_number), "pin test complete")
        return True

    def set_pixel(self, color):
        if color == "off":
            color = (0, 0, 0)
        elif isinstance(color, dict):
            color = (
                color.get("r", 0),
                color.get("g", 0),
                color.get("b", 0),
            )
        values = list(color[:3])
        while len(values) < 3:
            values.append(0)
        color = tuple(max(0, min(255, int(value))) for value in values)
        self.pixel_color = color
        self._write_pixel(color)
        log("port{}".format(self.port_number), "demon knocker pixel {}".format(color))

    def state(self):
        return {
            "mode": "demon_knocker",
            "a": self._solenoid_enabled(),
            "b": "neopixel",
            "solenoid_on": self._solenoid_enabled(),
            "solenoid_pulse_active": self.solenoid_deadline is not None,
            "pin_test_active": self.test_step is not None,
            "pin_test_step": self.test_step,
            "pixel": list(self.pixel_color),
            "pixel_color_order": self.pixel_color_order,
            "prop": self.metadata.get("prop"),
            "knocker": self.metadata.get("knocker"),
        }

    def safe_defaults(self):
        self._set_solenoid(False)
        self.solenoid_deadline = None
        self.test_step = None
        self.test_deadline = None
        self.pixel_data.value(0)
        self.set_pixel((0, 0, 0))

    def _write_pixel(self, color):
        color = self._physical_pixel_color(color)
        for index in range(self.pixel_count):
            self.pixels[index] = color
        self.pixels.write()

    def _physical_pixel_color(self, color):
        channels = {
            "R": color[0],
            "G": color[1],
            "B": color[2],
        }
        order = str(self.pixel_color_order).upper()
        if len(order) != 3:
            order = "RGB"
        return tuple(channels.get(channel, 0) for channel in order[:3])

    def _set_solenoid(self, enabled):
        if self.solenoid_active_low:
            self.solenoid.value(0 if enabled else 1)
        else:
            self.solenoid.value(1 if enabled else 0)

    def _solenoid_enabled(self):
        value = bool(self.solenoid.value())
        return not value if self.solenoid_active_low else value


class MorseboardHardware:
    def __init__(self):
        self.power_5v = Pin(pins.PROP_POWER_ENABLE, Pin.OUT)
        self.relay = Pin(pins.OPTIONAL_RELAY, Pin.OUT)
        self.dfplayer = DFPlayer()
        self.ports = []
        self.events = []
        self.dirty = True
        self.sequence_steps = []
        self.sequence_index = 0
        self.sequence_knocks_remaining = 0
        self.sequence_pulse_index = 0
        self.sequence_phase = None
        self.sequence_deadline = None
        self.sequence_current_port = None
        self.sequence_current_step = None

        self.power_5v.value(1 if config.PROP_5V_ENABLED_AT_BOOT else 0)
        self.relay.value(1 if config.RELAY_ENABLED_AT_BOOT else 0)

        for index, pair in enumerate(pins.PORT_PINS):
            port_number = index + 1
            rfid_metadata = config.RFID_INPUT_PORTS.get(port_number)
            candle_metadata = config.CANDLE_PORTS.get(port_number)
            demon_knocker_metadata = config.DEMON_KNOCKER_PORTS.get(port_number)
            if candle_metadata is not None:
                self.ports.append(
                    CandlePort(
                        port_number,
                        pair[0],
                        pair[1],
                        metadata=candle_metadata,
                    )
                )
            elif demon_knocker_metadata is not None:
                self.ports.append(
                    DemonKnockerPort(
                        port_number,
                        pair[0],
                        pair[1],
                        metadata=demon_knocker_metadata,
                    )
                )
            elif rfid_metadata is not None:
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

    def _is_candle(self, port):
        return isinstance(port, CandlePort)

    def _is_demon_knocker(self, port):
        return isinstance(port, DemonKnockerPort)

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
        if command.get("test_pins") and hasattr(port, "start_pin_test"):
            port.start_pin_test(now_ms, command.get("duration_ms", 500))
            self.dirty = True
            return
        if self._is_rfid_input(port):
            port.command(command, now_ms)
            return
        if self._is_candle(port):
            port.command(command, now_ms)
            self.dirty = True
            return
        if self._is_demon_knocker(port):
            port.command(command, now_ms)
            self.dirty = True
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

    def command_demon_led(self, led_number, command):
        port = self._demon_knocker_by_number(int(led_number))
        if port is None:
            log("demon_led", "ignored invalid led {}".format(led_number))
            return
        if command.get("off"):
            port.set_pixel((0, 0, 0))
            self.dirty = True
            return
        color = self._command_pixel(command)
        if color is None:
            log("demon_led", "ignored led {} without pixel".format(led_number))
            return
        port.set_pixel(color)
        self.dirty = True

    def command_demon_knocker(self, knocker_number, command, now_ms):
        port = self._demon_knocker_by_number(int(knocker_number))
        if port is None:
            log("demon_knocker", "ignored invalid knocker {}".format(knocker_number))
            return
        if command.get("stop"):
            self.stop_sequence()
            return
        if command.get("off"):
            port.command({"off": True}, now_ms)
            self.dirty = True
            return

        step = dict(command)
        step["knocker"] = int(knocker_number)
        if self._command_pixel(step) is not None and "pixel_pulse" not in step:
            step["pixel_pulse"] = True
        self.command_sequence({"steps": [step]}, now_ms)

    def command_sequence(self, command, now_ms):
        if command.get("stop"):
            self.stop_sequence()
            return

        steps = command.get("steps")
        if steps is None:
            steps = command.get("sequence")
        if not steps:
            log("sequence", "ignored empty sequence")
            return

        defaults = {
            "knock_ms": command.get(
                "default_knock_ms",
                getattr(config, "DEMON_KNOCKER_PULSE_MS", 120),
            ),
            "pause_ms": command.get("default_pause_ms", 150),
            "after_ms": command.get("default_after_ms", 0),
            "pixel": command.get("default_pixel", [255, 255, 255]),
            "pixel_pulse": command.get("pixel_pulse", False),
        }

        normalized = []
        for step in steps:
            if not hasattr(step, "get"):
                log("sequence", "ignored invalid step")
                continue
            action = self._sequence_action(step)
            if action == "led":
                port = self._sequence_demon_port(step, led_step=True)
                if port is None:
                    log("sequence", "ignored invalid demon led step")
                    continue
                color = self._command_pixel(step)
                if color is None:
                    log("sequence", "ignored demon led step without pixel")
                    continue
                normalized.append({
                    "type": "led",
                    "port": port.port_number,
                    "knocker": port.metadata.get("knocker"),
                    "pixel": color,
                    "after_ms": self._nonnegative_int(
                        step.get("after_ms", defaults["after_ms"]),
                        defaults["after_ms"],
                    ),
                })
                continue

            port = self._sequence_demon_port(step, led_step=False)
            if port is not None:
                knocker_number = port.metadata.get("knocker")
            else:
                knocker_number = self._int_or_none(
                    step.get("knocker", step.get("demon_knocker")),
                )
                log("sequence", "ignored step without valid knocker")
                continue

            if port is None:
                log("sequence", "ignored invalid knocker {}".format(knocker_number))
                continue

            pulses = self._sequence_pulses(step, defaults)
            if not pulses:
                log("sequence", "ignored knocker {} with no pulses".format(knocker_number))
                continue
            normalized.append({
                "type": "knocker",
                "port": port.port_number,
                "knocker": knocker_number,
                "pulses": pulses,
                "after_ms": self._nonnegative_int(
                    step.get("after_ms", defaults["after_ms"]),
                    defaults["after_ms"],
                ),
            })

        if not normalized:
            log("sequence", "ignored sequence with no usable steps")
            return

        self.stop_sequence()
        self.sequence_steps = normalized
        self.sequence_index = 0
        self.sequence_phase = "start_step"
        self.sequence_deadline = now_ms
        self.dirty = True
        log("sequence", "started {} steps".format(len(normalized)))

    def stop_sequence(self):
        if self.sequence_phase is not None:
            log("sequence", "stopped")
        if self.sequence_current_port is not None:
            self.sequence_current_port.command({"off": True}, 0)
        self.sequence_steps = []
        self.sequence_index = 0
        self.sequence_knocks_remaining = 0
        self.sequence_pulse_index = 0
        self.sequence_phase = None
        self.sequence_deadline = None
        self.sequence_current_port = None
        self.sequence_current_step = None
        self.dirty = True

    def update(self, now_ms):
        changed = False
        changed_rfid_ports = []
        changed_candle_ports = []
        for port in self.ports:
            if port.update(now_ms):
                changed = True
                if self._is_rfid_input(port):
                    changed_rfid_ports.append(port)
                elif self._is_candle(port):
                    changed_candle_ports.append(port)
        if self._update_sequence(now_ms):
            changed = True
        for port in changed_rfid_ports:
            event = port.event()
            event["readers"] = self.rfid_reader_statuses()
            event["all_correct"] = self.all_rfid_readers_correct()
            self.events.append(("rfid", event))
        for port in changed_candle_ports:
            event = port.event()
            event["candles"] = self.candle_statuses()
            self.events.append(("candle", event))
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

    def candle_statuses(self):
        return [
            port.candle_status()
            for port in self.ports
            if self._is_candle(port)
        ]

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
        candles = self.candle_statuses()
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
            "candles": candles,
            "sequence": {
                "active": self.sequence_phase is not None,
                "step_index": self.sequence_index,
                "pulse_index": self.sequence_pulse_index,
                "phase": self.sequence_phase,
            },
        }

    def safe_defaults(self):
        self.set_power(config.PROP_5V_ENABLED_AT_BOOT)
        self.set_relay(False)
        for port in self.ports:
            if self._is_rfid_input(port):
                port.safe_defaults()
            elif self._is_candle(port):
                port.safe_defaults()
            elif self._is_demon_knocker(port):
                port.safe_defaults()
            else:
                port.set_a(False)
                port.set_b(False)
        self.stop_sequence()
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

    def _update_sequence(self, now_ms):
        if self.sequence_phase is None:
            return False
        if ticks_diff(now_ms, self.sequence_deadline) < 0:
            return False

        if self.sequence_phase == "start_step":
            if self.sequence_index >= len(self.sequence_steps):
                self.sequence_phase = None
                self.sequence_current_port = None
                self.sequence_current_step = None
                log("sequence", "complete")
                return True
            step = self.sequence_steps[self.sequence_index]
            self.sequence_current_step = step
            self.sequence_current_port = self.ports[step["port"] - 1]
            self.sequence_pulse_index = 0
            if step["type"] == "led":
                self.sequence_current_port.set_pixel(step["pixel"])
                self.sequence_phase = "after_step"
                self.sequence_deadline = ticks_add(now_ms, step["after_ms"])
                log(
                    "sequence",
                    "demon led {} pixel {}".format(step["knocker"], step["pixel"]),
                )
                return True
            self.sequence_phase = "knock"
            return self._update_sequence(now_ms)

        if self.sequence_phase == "knock":
            if self.sequence_pulse_index >= len(self.sequence_current_step["pulses"]):
                self.sequence_phase = "after_step"
                self.sequence_deadline = ticks_add(
                    now_ms,
                    self.sequence_current_step["after_ms"],
                )
                return True
            pulse = self.sequence_current_step["pulses"][self.sequence_pulse_index]
            if pulse["pixel_pulse"]:
                self.sequence_current_port.set_pixel(pulse["pixel"])
            self.sequence_current_port.knock(
                now_ms,
                pulse["knock_ms"],
            )
            self.sequence_phase = "pause"
            self.sequence_deadline = ticks_add(
                now_ms,
                pulse["knock_ms"],
            )
            log(
                "sequence",
                "knocker {} pulse {}".format(
                    self.sequence_current_step["knocker"],
                    self.sequence_pulse_index + 1,
                ),
            )
            return True

        if self.sequence_phase == "pause":
            pulse = self.sequence_current_step["pulses"][self.sequence_pulse_index]
            if pulse["pixel_pulse"]:
                self.sequence_current_port.set_pixel((0, 0, 0))
            self.sequence_pulse_index += 1
            if self.sequence_pulse_index < len(self.sequence_current_step["pulses"]):
                self.sequence_phase = "knock"
                self.sequence_deadline = ticks_add(
                    now_ms,
                    pulse["pause_ms"],
                )
            else:
                self.sequence_phase = "after_step"
                self.sequence_deadline = ticks_add(
                    now_ms,
                    self.sequence_current_step["after_ms"],
                )
            return True

        if self.sequence_phase == "after_step":
            self.sequence_index += 1
            self.sequence_phase = "start_step"
            self.sequence_deadline = now_ms
            return True

        self.stop_sequence()
        return True

    def _int_or_none(self, value):
        try:
            return int(value)
        except Exception:
            return None

    def _nonnegative_int(self, value, default):
        parsed = self._int_or_none(value)
        if parsed is None:
            parsed = self._int_or_none(default)
        if parsed is None:
            parsed = 0
        return max(0, parsed)

    def _demon_knocker_by_number(self, knocker_number):
        for port in self.ports:
            if (
                self._is_demon_knocker(port)
                and self._int_or_none(port.metadata.get("knocker")) == knocker_number
            ):
                return port
        return None

    def _demon_knocker_by_port(self, port_number):
        if port_number < 1 or port_number > len(self.ports):
            return None
        port = self.ports[port_number - 1]
        if self._is_demon_knocker(port):
            return port
        return None

    def _sequence_action(self, step):
        action = step.get("action", step.get("type"))
        if action:
            action = str(action).lower()
            if action in ("led", "demon_led", "pixel"):
                return "led"
            if action in ("knock", "knocker", "demon_knocker"):
                return "knocker"
        if step.get("demon_led") is not None or step.get("led") is not None:
            return "led"
        return "knocker"

    def _sequence_demon_port(self, step, led_step=False):
        key = "led" if led_step else "knocker"
        target = self._int_or_none(step.get(key))
        if target is None:
            target = self._int_or_none(step.get("demon_{}".format(key)))
        if target is not None:
            return self._demon_knocker_by_number(target)
        port_number = self._int_or_none(step.get("port"))
        if port_number is not None:
            return self._demon_knocker_by_port(port_number)
        return None

    def _command_pixel(self, command):
        for name in ("pixel", "rgb", "color", "colour"):
            if name in command:
                return command[name]
        return None

    def _sequence_pulses(self, step, defaults):
        pulses = step.get("pulses")
        if pulses:
            return [
                self._normalize_pulse(pulse, step, defaults)
                for pulse in pulses
            ]

        knock_values = step.get("knock_ms", step.get("duration_ms"))
        if not isinstance(knock_values, (list, tuple)):
            knocks = self._nonnegative_int(step.get("knocks", 1), 1)
            knock_values = [
                step.get("knock_ms", step.get("duration_ms", defaults["knock_ms"]))
            ] * knocks

        pause_values = step.get("pause_ms", defaults["pause_ms"])
        normalized = []
        for index, knock_ms in enumerate(knock_values):
            normalized.append(
                self._normalize_pulse(
                    {
                        "knock_ms": knock_ms,
                        "pause_ms": self._list_value(pause_values, index, defaults["pause_ms"]),
                    },
                    step,
                    defaults,
                )
            )
        return normalized

    def _normalize_pulse(self, pulse, step, defaults):
        if hasattr(pulse, "get"):
            knock_ms = pulse.get("knock_ms", defaults["knock_ms"])
            if "duration_ms" in pulse:
                knock_ms = pulse.get("duration_ms")
            pause_ms = pulse.get("pause_ms", step.get("pause_ms", defaults["pause_ms"]))
            pixel = self._command_pixel(pulse)
            if pixel is None:
                pixel = self._command_pixel(step)
            if pixel is None:
                pixel = defaults["pixel"]
            pixel_pulse = pulse.get(
                "pixel_pulse",
                step.get("pixel_pulse", defaults["pixel_pulse"]),
            )
        else:
            knock_ms = pulse
            pause_ms = step.get("pause_ms", defaults["pause_ms"])
            pixel = self._command_pixel(step)
            if pixel is None:
                pixel = defaults["pixel"]
            pixel_pulse = step.get("pixel_pulse", defaults["pixel_pulse"])
        return {
            "knock_ms": self._nonnegative_int(knock_ms, defaults["knock_ms"]),
            "pause_ms": self._nonnegative_int(pause_ms, defaults["pause_ms"]),
            "pixel": pixel,
            "pixel_pulse": bool(pixel_pulse),
        }

    def _list_value(self, value, index, default):
        if isinstance(value, (list, tuple)):
            if index < len(value):
                return value[index]
            return default
        return value
