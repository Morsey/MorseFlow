# Morseboard Firmware

MicroPython skeleton for MorseFlow controller boards.

## Target Boards

- WIZnet W5500-EVB-Pico.
- WIZnet W5500-EVB-Pico2.

Flash board-specific W5500-enabled MicroPython firmware before copying these
files to the board.

## Deployment

Upload these files from this folder to the board filesystem:

- `boot.py`
- `app.py`
- `config.py`
- `debug.py`
- `pins.py`
- `messages.py`
- `dfplayer.py`
- `hardware.py`
- `ethernet.py`
- `mqtt_client.py`
- `mqtt_service.py`

Edit `config.py` for the site, room, board ID, MQTT broker, and network mode.

Do not upload a file named `main.py` for the Morseboard runtime. MorseFlow uses
`app.py`, and `boot.py` imports it and starts `app.main()`.

During development, open `app.py` in VS Code and use MicroPico Run. The guarded
entry point at the bottom of `app.py` starts `main()` only when the file is run
directly, while still allowing `boot.py` to import `app` safely.

The project bundles a lightweight MQTT client as `mqtt_client.py`. It is a
single top-level file so it can be uploaded through VS Code MicroPico without
needing nested folder support.

## Behavior

- Boots to safe defaults.
- Keeps switched 5V off by default.
- Keeps optional relay off by default.
- Keeps all prop signal outputs low by default.
- Uses state-machine updates for timed prop pulses.
- Retries Ethernet and MQTT reconnects indefinitely.
- Waits for a valid Ethernet IP before starting MQTT.
- Does not enter the MQTT service until the network is ready.
- Reports network connect/disconnect transitions to the REPL log.
- Uses MQTT Last Will and Testament for offline detection.
- Publishes retained status/state after MQTT reconnect.
- Prints debug/status messages to the USB REPL when `DEBUG_REPL` is enabled.

## USB REPL

MicroPython exposes the USB serial REPL by default on the Pico-class boards.
`boot.py` keeps that default intact and explicitly enables Ctrl-C interruption.

When the Morseboard is connected over USB, use the normal MicroPython serial
device from VS Code MicroPico, Thonny, or another serial terminal. Do not
redirect or disable `dupterm`, and do not move the REPL onto UART0 because
UART0 is reserved for the DFPlayer Mini on GPIO0/GPIO1.

`boot.py` does not detect USB power. It always imports `app` and starts
`app.main()`. When a USB REPL is attached, press Ctrl-C to interrupt the running
app and return to the REPL.

Set `DEBUG_REPL = False` in `config.py` to silence MorseFlow debug output.

## Debug Logs

Debug logs go to MicroPython stdout, which means they are visible in the USB
REPL only while a REPL is attached. Boot logs can happen before VS Code opens
the REPL, so `debug.py` also keeps a small in-memory buffer.

From the REPL:

```python
import debug
debug.dump()
```

To clear the buffer:

```python
debug.clear()
```

To start the app manually and watch live logs:

```python
import app
app.main()
```

Alternatively, use MicroPico Run on `app.py` from VS Code.

If you see `wiznet5k_send_ethernet: fatal error -5`, the W5500 driver is
reporting a network send failure. Check the Ethernet cable/link lights, confirm
the MQTT broker IP in `config.py`, and confirm the broker is reachable on the
wired network. For bench testing without Ethernet/MQTT, set
`MQTT_ENABLED = False` in `config.py`.
