# Firmware Notes

## Morseboard Firmware

The firmware skeleton in `firmware/morseboard/` is written for MicroPython.
It assumes a W5500-enabled firmware build for the specific WIZnet board.

Main modules:

- `main.py` - runtime entrypoint and service loop.
- `config.py` - board identity, MQTT settings, and static network options.
- `pins.py` - pin assignments for W5500, DFPlayer, prop power, relay, and ports.
- `hardware.py` - local IO abstractions and safe defaults.
- `mqtt_service.py` - MQTT connection, subscriptions, LWT, reconnect, and dispatch.
- `messages.py` - JSON command parsing and response payload helpers.

## Non-Blocking Rules

- Do not use blocking sleeps for prop actions.
- Use `time.ticks_ms()` and `time.ticks_diff()` for scheduling.
- Each subsystem exposes an `update(now_ms)` method.
- The main loop calls subsystem updates frequently.
- MQTT reconnect attempts are rate-limited and retried forever.

Short loop idling is acceptable to avoid a tight CPU spin, but prop timing
must not depend on `sleep()` calls.

