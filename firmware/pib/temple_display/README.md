# Temple Display Controller

MicroPython firmware for a Raspberry Pi Pico W controlling a MedeaWiz Sprite
4K over its TTL serial connection. Videos can be selected by active-low push
buttons or through a web page and HTTP API on the local Wi-Fi network.

## Wiring

| Pico W | Sprite 4K | Purpose |
| --- | --- | --- |
| GP0 / UART0 TX | Player RX, I/O pin 2 / red RCA centre | Commands to player |
| GP1 / UART0 RX | Player TX, I/O pin 3 / yellow RCA centre | Optional feedback |
| GND | I/O pin 4 / RCA shields | Common signal ground |

The Sprite serial port uses 3.3-5 V TTL levels, not conventional bipolar
RS-232 voltage levels. Do not connect a PC RS-232 port directly. The Sprite's
I/O pin 1/white RCA is a 5 V output; it is not needed when the Pico W has its
own USB power supply.

Serial commands and wiring follow the
[MedeaWiz Sprite 4K manual](https://www.medeawiz.com/Downloads.html).

Each button connects its configured GPIO directly to GND. The firmware enables
the Pico's internal pull-up resistors.

| GPIO | Action |
| --- | --- |
| GP10 | Play `000` |
| GP11 | Play `001` |
| GP12 | Play `002` |
| GP13 | Play `003` |
| GP14 | Pause/resume |
| GP15 | Stop/blank using Sprite sleep |

## Sprite Setup

In the Sprite setup menu select:

- Play Mode: **Video Control Mode**
- Control Mode: **Serial Control**
- Baud Rate: **9600** (or match `SPRITE_BAUDRATE`)
- Address Mode: **Do not use Address**

Place the looping/idle video on the Sprite media as `000.<extension>`. Trigger
videos are named `001.<extension>` through `200.<extension>`. A play command is
one numeric byte; the firmware deliberately sends no line ending.

## Installation

1. Install a current Pico W MicroPython build.
2. Set `WIFI_SSID` and `WIFI_PASSWORD` at the top of `main.py`.
3. Copy `main.py` to the Pico W filesystem root.
4. Reboot and read the assigned URL from the USB serial REPL.

The physical buttons continue working if Wi-Fi is unavailable.

Set the Sprite's Serial Feedback option to the desired reporting mode. Incoming
bytes are decoded into readable messages, printed to the USB REPL, and retained
as the 10 most recent timestamped entries. The web page refreshes that history
every two seconds. The Pico attempts to synchronize its clock from NTP and uses
UTC timestamps; if synchronization is unavailable, timestamps show uptime.
Since Sprite feedback may
echo commands as well as report player state, the page labels file-number bytes
without assuming that every returned byte represents a new playback event.

At startup, the Pico waits for `STARTUP_TEST_DELAY_MS` and then sends the
Sprite's request-current-file command (`0xCC`). A received response produces a
`PASSED` message on the REPL;
no response before the configured timeout produces a diagnostic `FAILED`
message. The same connection-test state appears on the web page. This confirms
two-way serial communication, so the Sprite TX connection to Pico RX and its
Serial Feedback setting must be enabled for the test to pass.

## HTTP Control

The root URL serves a simple control page with direct controls for files `000`,
`001`, `002`, and `003`, plus pause/resume and stop/blank controls.
Change `WEB_FILES` near the top of `main.py` if the displayed selection changes.

```text
POST /api/play?file=1
POST /api/pause-resume
POST /api/stop
POST /api/wake
POST /api/sleep
GET  /api/status
GET  /api/help
```

`/api/status` includes the last command, the most recently received raw bytes,
and the recent timestamped serial-feedback history.

Example from another device on the LAN:

```bash
curl -X POST http://temple-display.local/api/play?file=3
```

There is currently no authentication or TLS, so this service should only be
used on a trusted, isolated show-control LAN.

The page embeds the API description as JSON for automation clients, and
`GET /api/help` returns the same control instructions in machine-readable form.
