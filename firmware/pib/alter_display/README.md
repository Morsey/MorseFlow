# Alter Display PIB

Test firmware for a Raspberry Pi Pico driving 2.42-inch SPI OLED displays.

## Wiring

Shared by all displays:

| OLED pin | Pico GPIO |
| --- | --- |
| GND | GND |
| VCC | 3V3 or external regulated 3.3V |
| SCK | GPIO10 |
| SDA | GPIO11 |
| DC | GPIO12 |
| RES | GPIO15 |

Separate chip selects:

| Display | OLED CS |
| --- | --- |
| 1 | GPIO2 |
| 2 | GPIO3 |
| 3 | GPIO4 |
| 4 | GPIO5 |
| 5 | GPIO6 |

Screen 1 KY-040 rotary encoder:

| KY-040 pin | Pico GPIO |
| --- | --- |
| GND | GND |
| + | 3V3 |
| CLK | GPIO7 |
| DT | GPIO8 |
| SW | GPIO9 |

Use a common ground if the displays are powered from an external 3.3V supply.
The numbers above are GPIO numbers, not physical package pin numbers.

## Test

Upload these files to the Pico filesystem root:

- `boot.py`
- `main.py`
- `config.py`
- `onboard_led.py`
- `test_display.py`
- `OLED-1.bin` through `OLED-10.bin`, or any other `1024` byte `.bin` images

From the REPL:

```python
import test_display
test_display.main()
```

By default, only display 1 on `GPIO2` is active. Rotate the KY-040 encoder to
step through `OLED-1.bin` through `OLED-10.bin` from the Pico root. Press the
knob to reset to `OLED-1.bin`.
Press Ctrl-C to stop and turn the displays off.

## Boot

This prop uses the same boot pattern as the Morseboards:

- `boot.py` keeps the default USB serial REPL enabled and enables Ctrl-C.
- `main.py` waits briefly before auto-starting the configured test/app module.
- The onboard LED flashes at 10 Hz during the startup pause window.
- Press Ctrl-C during that window to skip auto-start and stay at the REPL.

The current auto-start target is configured in `config.py`:

```python
AUTO_RUN_MODULE = "test_network_mqtt"
AUTO_RUN_FUNCTION = "main"
```

For display-only testing, change `AUTO_RUN_MODULE` to `"test_display"`.

## Network/MQTT Test

Upload these extra files to the Pico filesystem root:

- `mqtt_client.py`
- `test_network_mqtt.py`

Check these settings in `config.py` before running:

- `MQTT_HOST`
- `MQTT_CLIENT_ID`
- `MQTT_TOPIC_ROOT`
- `NETWORK_DHCP`

From the REPL:

```python
import test_network_mqtt
test_network_mqtt.main()
```

The test uses the W5500 Ethernet pins on the W5500-EVB-Pico/Pico2:

| W5500 signal | Pico GPIO |
| --- | --- |
| MISO | GPIO16 |
| CS | GPIO17 |
| SCK | GPIO18 |
| MOSI | GPIO19 |
| RST | GPIO20 |

It publishes status to:

```text
morseflow/prodigy/cmcm/pib-alter-display/status
```

and heartbeat messages to:

```text
morseflow/prodigy/cmcm/pib-alter-display/heartbeat
```

It subscribes to:

```text
morseflow/prodigy/cmcm/pib-alter-display/cmd/#
```

Send a test message to:

```text
morseflow/prodigy/cmcm/pib-alter-display/cmd/test
```

Example payload:

```json
{"test":"hello"}
```

Received MQTT messages are printed to the REPL. Press Ctrl-C to stop.

Animation speed is controlled in `config.py`:

- `OLED_FRAME_DELAY_MS`: delay between frames.
- `OLED_SWEEP_STEP_PIXELS`: how far the vertical line moves each frame.

Encoder behavior is controlled in `config.py`:

- `ENCODER_STEPS_PER_DETENT`: set to `4` for most KY-040 modules; try `2` if
  turns feel unresponsive.
- `ENCODER_DEBOUNCE_MS`: increase slightly if numbers still skip.

## Image Files

The Pico test displays raw `1024` byte `.bin` files from the Pico root.
JPG and PNG files must be converted first on your computer:

```bash
python3 -m pip install pillow
python3 firmware/pib/alter_display/tools/convert_images.py
```

The converter writes `.bin` files next to the source images. Upload the `.bin`
files to the Pico root.

If all displays stay blank:

- Confirm `SDA` on the OLED is wired to Pico `GPIO11`; on SPI OLEDs this is
  MOSI/DIN, not I2C SDA.
- Confirm `RES` is wired to Pico `GPIO15`.
- Confirm each display has its own `CS` line on `GPIO2` through `GPIO6`.
- If the panels are powered from an external supply, connect supply ground to
  Pico ground.
- Try changing `OLED_CONTROLLER` in `config.py` from `"ssd1309"` to
  `"ssd1306"`.
