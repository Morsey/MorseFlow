# E-Paper Display PIB

Standalone Pico-class Prop Interface Board for a Waveshare 7.3-inch seven-color
e-paper display.

This PIB is not connected to a Morseboard. It uses its own W5500 Ethernet
connection for HTTP file management and MQTT display commands.

## Runtime Upload

Upload these files to the Pico filesystem root for the networked runtime:

- `boot.py`
- `main.py`
- `app.py`
- `config.py`
- `debug.py`
- `display_controller.py`
- `epaper_display.py`
- `ethernet.py`
- `http_service.py`
- `messages.py`
- `mqtt_client.py`
- `mqtt_service.py`
- `onboard_led.py`

Upload image buffers into an `images/` folder on the Pico, or upload them later
through the HTTP web interface. `boot.py` keeps the USB REPL available, and
`main.py` starts the configured runtime after the recovery window.

## Boot

The startup flow matches the Morseboard firmware:

- `boot.py` enables Ctrl-C on the USB serial REPL and returns quickly.
- `main.py` flashes the onboard LED at 10 Hz while waiting briefly before
  auto-start.
- Press Ctrl-C during that window to skip auto-start and stay at the REPL.
- If not interrupted, `main.py` imports the module named by `AUTO_RUN_MODULE`
  and calls `AUTO_RUN_FUNCTION`.

For the full display runtime:

```python
AUTO_RUN_MODULE = "app"
AUTO_RUN_FUNCTION = "main"
```

For the network/MQTT-only test, set `AUTO_RUN_MODULE = "test_network_mqtt"` or
run `test_network_mqtt.main()` manually from the REPL.

## Network/MQTT Test

Upload these files to the Pico filesystem root:

- `boot.py`
- `main.py`
- `config.py`
- `debug.py`
- `ethernet.py`
- `messages.py`
- `mqtt_client.py`
- `onboard_led.py`
- `test_network_mqtt.py`

Run manually from the REPL if auto-start is interrupted:

```python
import test_network_mqtt
test_network_mqtt.main()
```

The test publishes retained status to:

```text
morseflow/prodigy/cmcm/epaper-001/status
```

It publishes heartbeat messages every 10 seconds to:

```text
morseflow/prodigy/cmcm/epaper-001/heartbeat
```

It subscribes to:

```text
morseflow/prodigy/cmcm/epaper-001/cmd/#
```

Send a test message to:

```text
morseflow/prodigy/cmcm/epaper-001/cmd/test
```

Example payload:

```json
{"test":"hello"}
```

## HTTP

When the board has an IP address, open it in a browser:

```text
http://<board-ip>/
```

The web page can upload `.bin` files, list images, delete images, display an
image, and clear the panel to white or black. The home page scans the device for
all `.bin` files in `images/` and the filesystem root, then lets the user select
any detected image from a dropdown and show it.

HTTP API endpoints:

- `GET /status`
- `GET /images`
- `PUT /images/<name>.bin` with the raw `192000` byte file body
- `DELETE /images/<name>.bin`
- `POST /show?image=<name>.bin`
- `POST /show?color=white`
- `POST /show?color=black`

## MQTT

Default topic root:

```text
morseflow/prodigy/cmcm/epaper-001
```

Published topics:

- `morseflow/prodigy/cmcm/epaper-001/status` retained online/offline heartbeat.
- `morseflow/prodigy/cmcm/epaper-001/state` retained display/file state.
- `morseflow/prodigy/cmcm/epaper-001/event` live display/file/error events.

Command topics:

```text
morseflow/prodigy/cmcm/epaper-001/cmd/show
{"image":"E ink Scare.bin"}
```

```text
morseflow/prodigy/cmcm/epaper-001/cmd/clear
{"color":"white"}
```

```text
morseflow/prodigy/cmcm/epaper-001/cmd/delete
{"image":"old-image.bin"}
```

```text
morseflow/prodigy/cmcm/epaper-001/cmd/status
{}
```

The runtime publishes status before and after slow display refreshes so
controllers can see when an image change starts, completes, or fails.

## Display Test

Upload these files to the Pico filesystem root:

- `config.py`
- `epaper_display.py`
- `test_display.py`
- `E ink Non Scare.bin`
- `E ink Scare.bin`

From the REPL:

```python
import test_display
test_display.main()
```

The test initializes the panel and displays `E ink Non Scare.bin`. Press Enter
in the REPL to alternate between the non-scare and scare images. Press Ctrl-C to
stop and put the display to sleep.

## Default Wiring

These defaults match the previous reference project for the display and use
SPI0 for the W5500 Ethernet interface.

| E-paper function | GPIO |
| --- | --- |
| SPI bus | SPI1 |
| CS | GPIO9 |
| DC | GPIO8 |
| RST | GPIO12 |
| BUSY | GPIO13 |
| SCK | GPIO10 |
| MOSI | GPIO11 |

| W5500 function | GPIO |
| --- | --- |
| SPI bus | SPI0 |
| MISO | GPIO16 |
| CS | GPIO17 |
| SCK | GPIO18 |
| MOSI | GPIO19 |
| RST | GPIO20 |

Edit `config.py` if the panel is wired differently.

## Image Assets

Store editable/source images here:

```text
firmware/pib/epaper_display/images/source/
```

Store generated Pico-ready `.bin` display buffers here:

```text
firmware/pib/epaper_display/images/bin/
```

Copy only the `.bin` files needed for a test or runtime onto the Pico
filesystem.

## Convert Images

Install the desktop dependency once:

```bash
python3 -m pip install -r firmware/pib/epaper_display/requirements.txt
```

Put source images in:

```text
firmware/pib/epaper_display/images/source/
```

Convert all supported source images:

```bash
python3 firmware/pib/epaper_display/tools/convert_images.py
```

The converter rotates source images by 90 degrees before fitting them to the
panel's `800x480` buffer. To use a different orientation:

```bash
python3 firmware/pib/epaper_display/tools/convert_images.py --rotate 270
```

Generated `.bin` files are written to:

```text
firmware/pib/epaper_display/images/bin/
```

Each full-screen `.bin` file should be `192000` bytes.

## Test Log

### 2026-08-22 18:00 BST

- Status: display bring-up test passed.
- Software base: git commit `4a89ef6` plus uncommitted
  `firmware/pib/epaper_display/` files.
- Test run: `test_display.main()`.
- Observed behavior: color bars and `EPAPER / READY` screen displayed
  correctly; display sleep completed.
