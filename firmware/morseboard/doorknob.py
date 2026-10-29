try:
    import ujson as json
except ImportError:
    import json

from machine import I2C, Pin
from time import ticks_add, ticks_diff, ticks_ms

from debug import log


class DoorKnobPuzzle:
    ANGLE_REGISTER = 0x0C

    def __init__(self, metadata):
        self.metadata = metadata or {}
        self.sda_pin = int(self.metadata.get("sda_pin", 10))
        self.scl_pin = int(self.metadata.get("scl_pin", 11))
        self.address = int(self.metadata.get("address", 0x36))
        self.poll_ms = max(10, int(self.metadata.get("poll_ms", 50)))
        self.config_path = self.metadata.get("config_path", "doorknob_config.json")
        settings = dict(self.metadata)
        settings.update(self._load_saved_config())
        self._apply_settings(settings)

        self.i2c = I2C(
            int(self.metadata.get("i2c_id", 1)),
            sda=Pin(self.sda_pin),
            scl=Pin(self.scl_pin),
            freq=int(self.metadata.get("frequency", 10000)),
        )
        self.raw_angle = None
        self.angle_degrees = None
        self.previous_angle = None
        self.next_poll_ms = ticks_ms()
        self.step_index = 0
        self.step_travel_degrees = 0.0
        self.last_direction = None
        self.solved = False
        self.reset_deadline = None
        self.last_error = None
        log(
            "doorknob",
            "AS5600 initialized SDA=GPIO{} SCL=GPIO{} steps={}".format(
                self.sda_pin,
                self.scl_pin,
                len(self.sequence),
            ),
        )

    def claimed_pins(self):
        return {self.sda_pin, self.scl_pin}

    def update(self, now_ms):
        events = []
        changed = False

        if self.reset_deadline is not None and ticks_diff(now_ms, self.reset_deadline) >= 0:
            events.append(self.reset(now_ms, reason="auto_reset"))
            changed = True

        if ticks_diff(now_ms, self.next_poll_ms) < 0:
            return changed, events
        self.next_poll_ms = ticks_add(now_ms, self.poll_ms)

        try:
            raw_angle = self._read_raw_angle()
        except Exception as exc:
            error = repr(exc)
            if error != self.last_error:
                self.last_error = error
                events.append(self._event("error", error=error))
                changed = True
                log("doorknob", "AS5600 read failed {}".format(error))
            return changed, events

        recovered = self.last_error is not None
        self.last_error = None
        self.raw_angle = raw_angle
        self.angle_degrees = (raw_angle * 360.0) / 4096.0

        if recovered:
            events.append(self._event("recovered"))
            changed = True

        if self.previous_angle is not None and not self.solved and self.sequence:
            event = self._process_rotation(now_ms)
            if event is not None:
                events.append(event)
                changed = True
        self.previous_angle = self.angle_degrees
        return changed, events

    def update_config(self, command, now_ms=None):
        allowed = (
            "sequence",
            "tolerance_degrees",
            "target_overturn_degrees",
            "direction_deadband_degrees",
            "clockwise_sign",
            "auto_reset_ms",
        )
        settings = self.configuration()
        for name in allowed:
            if name in command:
                settings[name] = command[name]
        self._apply_settings(settings)
        if command.get("save"):
            self._save_config()
        event = self.reset(now_ms, reason="configured")
        event["saved"] = bool(command.get("save"))
        event["configuration"] = self.configuration()
        return event

    def reset(self, now_ms=None, reason="reset"):
        if now_ms is None:
            now_ms = ticks_ms()
        self.step_index = 0
        self.step_travel_degrees = 0.0
        self.last_direction = None
        self.solved = False
        self.reset_deadline = None
        self.previous_angle = self.angle_degrees
        log("doorknob", "puzzle reset")
        return self._event(reason)

    def state(self):
        return {
            "prop": self.metadata.get("prop", "door_knob"),
            "ready": self.angle_degrees is not None and self.last_error is None,
            "raw_angle": self.raw_angle,
            "angle_degrees": self._rounded_angle(),
            "step_index": self.step_index,
            "step_count": len(self.sequence),
            "next_step": self._next_step(),
            "last_direction": self.last_direction,
            "distance_to_target_degrees": self._distance_to_target(),
            "solved": self.solved,
            "error": self.last_error,
        }

    def repl_status(self):
        step = self._next_step()
        if step is None:
            target = "-"
            required_direction = "-"
            distance = "-"
        else:
            target = "{:.1f}".format(step["target_degrees"])
            required_direction = step["direction"]
            distance_value = self._distance_to_target()
            distance = "-" if distance_value is None else "{:.1f}".format(distance_value)
        angle = "-" if self.angle_degrees is None else "{:.1f}".format(self.angle_degrees)
        current_direction = self.last_direction or "still"
        return "angle={} target={} distance={} moving={} required={} step={}/{} travel={:.1f} solved={}".format(
            angle,
            target,
            distance,
            current_direction,
            required_direction,
            self.step_index + 1 if not self.solved else self.step_index,
            len(self.sequence),
            self.step_travel_degrees,
            int(self.solved),
        )

    def configuration(self):
        return {
            "sequence": [dict(step) for step in self.sequence],
            "tolerance_degrees": self.tolerance_degrees,
            "target_overturn_degrees": self.target_overturn_degrees,
            "direction_deadband_degrees": self.direction_deadband_degrees,
            "clockwise_sign": self.clockwise_sign,
            "auto_reset_ms": self.auto_reset_ms,
        }

    def _process_rotation(self, now_ms):
        delta = self._signed_difference(self.angle_degrees, self.previous_angle)
        clockwise_delta = delta * self.clockwise_sign
        if abs(clockwise_delta) < self.direction_deadband_degrees:
            self.last_direction = "still"
            return None

        direction = "cw" if clockwise_delta > 0 else "ccw"
        self.last_direction = direction
        step = self.sequence[self.step_index]
        required_direction = step["direction"]
        at_target = self._target_reached(step, direction)

        if required_direction != "either" and direction != required_direction:
            if at_target:
                previous_step = self.step_index
                event = self.reset(now_ms, reason="wrong_direction")
                event["previous_step_index"] = previous_step
                event["direction"] = direction
                return event
            return None

        self.step_travel_degrees += abs(clockwise_delta)
        if not at_target or self.step_travel_degrees < step["min_travel_degrees"]:
            return None

        reached_index = self.step_index
        reached_step = dict(step)
        self.step_index += 1
        self.step_travel_degrees = 0.0

        if self.step_index >= len(self.sequence):
            self.solved = True
            if self.auto_reset_ms:
                self.reset_deadline = ticks_add(now_ms, self.auto_reset_ms)
            log("doorknob", "safe combination success")
            return self._event(
                "success",
                reached_step_index=reached_index,
                reached_step=reached_step,
            )

        log("doorknob", "combination step {} accepted".format(reached_index + 1))
        return self._event(
            "step",
            reached_step_index=reached_index,
            reached_step=reached_step,
        )

    def _apply_settings(self, settings):
        sequence = settings.get("sequence", ())
        normalized = []
        for value in sequence:
            if hasattr(value, "get"):
                target = value.get("target_degrees", value.get("target"))
                direction = str(value.get("direction", "either")).lower()
                min_travel = value.get("min_travel_degrees", value.get("min_travel", 20.0))
            else:
                target = value
                direction = "either"
                min_travel = 20.0
            if target is None:
                raise ValueError("doorknob sequence step requires a target angle")
            if direction not in ("cw", "ccw", "either"):
                raise ValueError("doorknob direction must be cw, ccw, or either")
            normalized.append({
                "target_degrees": float(target) % 360.0,
                "direction": direction,
                "min_travel_degrees": max(0.0, float(min_travel)),
            })
        if not normalized:
            raise ValueError("doorknob sequence cannot be empty")
        self.sequence = tuple(normalized)
        self.tolerance_degrees = max(0.1, float(settings.get("tolerance_degrees", 10.0)))
        self.target_overturn_degrees = max(
            0.0,
            float(settings.get("target_overturn_degrees", 15.0)),
        )
        self.direction_deadband_degrees = max(
            0.0,
            float(settings.get("direction_deadband_degrees", 1.5)),
        )
        self.clockwise_sign = 1 if int(settings.get("clockwise_sign", 1)) >= 0 else -1
        self.auto_reset_ms = max(
            0,
            int(settings.get("auto_reset_ms", 2000)),
        )

    def _load_saved_config(self):
        try:
            with open(self.config_path, "r") as config_file:
                data = json.loads(config_file.read())
            if not hasattr(data, "get"):
                raise ValueError("saved doorknob config is not an object")
            log("doorknob", "loaded {}".format(self.config_path))
            return data
        except OSError:
            return {}
        except Exception as exc:
            log("doorknob", "ignored invalid saved config {}".format(repr(exc)))
            return {}

    def _save_config(self):
        with open(self.config_path, "w") as config_file:
            config_file.write(json.dumps(self.configuration()))
        log("doorknob", "saved {}".format(self.config_path))

    def _read_raw_angle(self):
        data = self.i2c.readfrom_mem(self.address, self.ANGLE_REGISTER, 2)
        if len(data) != 2:
            raise OSError("AS5600 returned {} bytes".format(len(data)))
        return ((data[0] << 8) | data[1]) & 0x0FFF

    def _event(self, reason, **extra):
        event = self.state()
        event["reason"] = reason
        event.update(extra)
        return event

    def _next_step(self):
        if self.solved or self.step_index >= len(self.sequence):
            return None
        return dict(self.sequence[self.step_index])

    def _distance_to_target(self):
        step = self._next_step()
        if step is None or self.angle_degrees is None:
            return None
        return round(
            self._circular_difference(
                self.angle_degrees,
                step["target_degrees"],
            ),
            2,
        )

    def _target_reached(self, step, approach_direction):
        offset = (
            self._signed_difference(self.angle_degrees, step["target_degrees"])
            * self.clockwise_sign
        )
        if approach_direction == "cw":
            return -self.tolerance_degrees <= offset <= self.target_overturn_degrees
        if approach_direction == "ccw":
            return -self.target_overturn_degrees <= offset <= self.tolerance_degrees
        return abs(offset) <= max(
            self.tolerance_degrees,
            self.target_overturn_degrees,
        )

    def _rounded_angle(self):
        if self.angle_degrees is None:
            return None
        return round(self.angle_degrees, 2)

    @staticmethod
    def _signed_difference(first, second):
        return (first - second + 180.0) % 360.0 - 180.0

    @staticmethod
    def _circular_difference(first, second):
        return abs((first - second + 180.0) % 360.0 - 180.0)
