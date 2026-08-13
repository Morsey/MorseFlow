# Firmware Notes

## Morseboard Firmware

The firmware skeleton in `firmware/morseboard/` is written for MicroPython.
It assumes a W5500-enabled firmware build for the specific WIZnet board.

Main modules:

- `boot.py` - keeps the default USB serial REPL available and conditionally starts the app.
- `app.py` - runtime entrypoint and service loop.
- `config.py` - shared defaults and board-specific override loader.
- `board_config.py` - active board identity, port roles, and per-board overrides.
- `board_configs/` - stored per-board config files; copy one to `board_config.py` before upload.
- `debug.py` - small REPL logging helper controlled by `DEBUG_REPL`.
- `pins.py` - pin assignments for W5500, DFPlayer, prop power, relay, and ports.
- `hardware.py` - local IO abstractions and safe defaults.
- `mqtt_client.py` - bundled lightweight MQTT client.
- `mqtt_service.py` - MQTT connection, subscriptions, LWT, reconnect, and dispatch.
- `messages.py` - JSON command parsing and response payload helpers.

## Non-Blocking Rules

- Do not use blocking sleeps for prop actions.
- Use `time.ticks_ms()` and `time.ticks_diff()` for scheduling.
- Each subsystem exposes an `update(now_ms)` method.
- The app loop calls subsystem updates frequently.
- MQTT reconnect attempts are rate-limited and retried forever.

Short loop idling is acceptable to avoid a tight CPU spin, but prop timing
must not depend on `sleep()` calls.

## USB REPL Access

Morseboard firmware must remain accessible through the Pico USB serial REPL
when connected by USB. The project does not disable MicroPython's default REPL
and does not redirect it to UART0, because UART0 is used by the DFPlayer Mini
on GPIO0/GPIO1.

`firmware/morseboard/boot.py` enables Ctrl-C interruption with
`micropython.kbd_intr(3)`. If the GPIO21 boot REPL button is held low during
boot, `boot.py` skips `app.main()` and leaves the board at the USB REPL. The app
firmware loop also calls `machine.idle()` each pass so the runtime stays
cooperative during development and recovery.

The Morseboard runtime is named `app.py`, not `main.py`. When the GPIO21 boot
REPL button is not held, `boot.py` imports `app` and starts `app.main()`. It
does not try to detect USB power or whether a serial terminal is attached.

For development, connect over the USB serial REPL and press Ctrl-C to interrupt
the running app. For manual testing, VS Code MicroPico can still run `app.py`
directly; the guarded entry point at the bottom of `app.py` starts `main()`
only when the file is run directly.

## REPL Debug Output

Firmware modules log useful boot, network, MQTT, hardware, audio, and prop-port
events to the USB REPL through `debug.py`. Set `DEBUG_REPL = False` in
`config.py` to silence this output for production boards.

Logs are plain MicroPython stdout. They are visible live only when the REPL is
attached at the moment the log line is printed. Because boot messages can happen
before VS Code opens the REPL, `debug.py` also keeps a small in-memory buffer.

From the REPL:

```python
import debug
debug.dump()
```

Use `debug.clear()` to clear the buffer. The buffer length is controlled by
`DEBUG_BUFFER_SIZE` in `config.py`.

If the REPL shows `wiznet5k_send_ethernet: fatal error -5`, the W5500 driver is
reporting a network send failure. Check the wired Ethernet link, broker IP, and
broker availability. For USB bench testing without MQTT traffic, set
`MQTT_ENABLED = False` in `config.py`.

MQTT startup is gated on a valid Ethernet IP address. The W5500 interface can
report a link-like connected state before DHCP has completed, so the firmware
waits until `ifconfig()[0]` is not `0.0.0.0` before connecting to the broker.
The app loop does not call into the MQTT service at all until this network-ready
condition is true.

When that condition changes, the app logs the transition. On successful network
connection, it reports the assigned IP address to the REPL log.

## Bundled MQTT Client

Some W5500-enabled MicroPython builds do not include `umqtt.simple`. MorseFlow
therefore bundles a local `firmware/morseboard/mqtt_client.py` module and
imports it directly from `mqtt_service.py`.

This avoids nested package upload issues in VS Code MicroPico. Copy
`mqtt_client.py` to the board at the same filesystem level as `app.py`,
`config.py`, and `mqtt_service.py`.

## Per-Board Config

The shared Morseboard firmware should stay identical across physical boards.
Only `board_config.py` should differ per board.

Stored board configs live in:

```text
firmware/morseboard/board_configs/
```

To prepare a board, copy the chosen stored config to the active filename:

```bash
cp firmware/morseboard/board_configs/mb_001.py firmware/morseboard/board_config.py
```

Then upload the common firmware files plus `board_config.py` to the board. The
runtime imports `board_config.py` from the board filesystem and applies any
uppercase settings it defines, such as `BOARD_ID`, `MQTT_HOST`, static IP
settings, or `RFID_INPUT_PORTS`.

Use unique board IDs such as `mb-001`, `mb-002`, and `mb-003`. MQTT topics are
then derived automatically:

```text
morseflow/<site>/<room>/<board_id>
```
