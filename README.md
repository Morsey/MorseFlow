# MorseFlow

MorseFlow is an escape-room prop control system. Node-RED owns the main room
and game logic and talks through an MQTT broker to wired Morseboard controller
boards. Standalone Prop Interface Boards may also provide focused local or
Wi-Fi-controlled functions.

## Project Layout

- `docs/` - hardware, architecture, MQTT, and firmware notes.
- `firmware/morseboard/` - shared MicroPython runtime and per-board profiles for WIZnet W5500-EVB-Pico and Pico2 Morseboards.
- `firmware/pib/` - standalone and prop-specific MicroPython controllers, including RFID, displays, sensors, and puzzles.
- `examples/` - sample configuration files and MQTT payloads.
- `node-red/flows/` - starter Node-RED flow examples.

## First Room

The first MorseFlow room is **The Curse of Mount Clifton Manor**, abbreviated
`CMCM`. The suggested MQTT room slug is `cmcm`.

CMCM is the concrete implementation target for now. See `docs/cmcm/` for the
living board, prop, MQTT, and test-plan notes. Production Node-RED flows are not
stored in this repository.

## Hardware Summary

- Morseboards use WIZnet W5500-EVB-Pico or W5500-EVB-Pico2 boards.
- Firmware is MicroPython with board-specific W5500 Ethernet support.
- Morseboards use wired Ethernet and do not use Wi-Fi.
- W5500 Ethernet pins are reserved: GPIO16-GPIO21.
- DFPlayer Mini: GPIO0 to DFPlayer RX, GPIO1 to DFPlayer TX.
- GPIO15 controls switched 5V prop power, normally enabled at boot and used for prop reset/recovery.
- 12V prop power is always live.
- GPIO22 may control an onboard relay when populated.
- Eight RJ45 prop ports expose GND, switched 5V, always-live 12V, Signal A, and Signal B.

## Current Status

The shared Morseboard firmware is deployed through profiles for MB-001 through
MB-010. It uses non-blocking state machines for safe GPIO control, timed pulses,
RFID and switch inputs, candles, NeoPixels, latch locks, ToF sensors, bookshelf
and doorknob puzzles, DFPlayer audio, Ethernet recovery, MQTT commands, retained
state, and live events.

Standalone PIB firmware includes the Pico W Temple Display controller, which
drives a MedeaWiz Sprite 4K over TTL serial from physical buttons or a small
HTTP control interface. See `firmware/pib/temple_display/README.md`.

## AI Assistance

MorseFlow has been developed with assistance from OpenAI Codex. See
`docs/ai-assistance.md` for details.

## License

This project is source-available for non-commercial use only. Commercial copying
or commercial use of the code is not permitted without prior written permission.
See `LICENSE.md`.
