# Morseboard Firmware

MicroPython skeleton for MorseFlow controller boards.

## Target Boards

- WIZnet W5500-EVB-Pico.
- WIZnet W5500-EVB-Pico2.

Flash board-specific W5500-enabled MicroPython firmware before copying these
files to the board.

## Deployment

Copy the files in this folder to the board filesystem:

- `main.py`
- `config.py`
- `pins.py`
- `messages.py`
- `dfplayer.py`
- `hardware.py`
- `ethernet.py`
- `mqtt_service.py`

Edit `config.py` for the site, room, board ID, MQTT broker, and network mode.

## Behavior

- Boots to safe defaults.
- Keeps switched 5V off by default.
- Keeps optional relay off by default.
- Keeps all prop signal outputs low by default.
- Uses state-machine updates for timed prop pulses.
- Retries Ethernet and MQTT reconnects indefinitely.
- Uses MQTT Last Will and Testament for offline detection.
- Publishes retained status/state after MQTT reconnect.

