# MorseFlow

MorseFlow is a wired MQTT-based escape room prop control framework.
Node-RED owns the main room/game logic and talks through an MQTT broker
to Morseboard controller boards.

## Project Layout

- `docs/` - hardware, architecture, MQTT, and firmware notes.
- `firmware/morseboard/` - MicroPython skeleton for WIZnet W5500-EVB-Pico and Pico2 Morseboards.
- `firmware/pib/rfid_reader/` - starter firmware notes/code for smart RFID Prop Interface Boards.
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
- No Wi-Fi.
- W5500 Ethernet pins are reserved: GPIO16-GPIO21.
- DFPlayer Mini: GPIO0 to DFPlayer RX, GPIO1 to DFPlayer TX.
- GPIO15 controls switched 5V prop power, normally enabled at boot and used for prop reset/recovery.
- 12V prop power is always live.
- GPIO22 may control an onboard relay when populated.
- Eight RJ45 prop ports expose GND, switched 5V, always-live 12V, Signal A, and Signal B.

## Current Status

This repository is an initial scaffold. The Morseboard firmware is structured
around non-blocking state-machine updates using `time.ticks_ms()`. It includes
safe IO defaults, timed prop pulses, MQTT reconnect hooks, status publishing,
and simple DFPlayer command support.

## AI Assistance

MorseFlow has been developed with assistance from OpenAI Codex. See
`docs/ai-assistance.md` for details.

## License

This project is source-available for non-commercial use only. Commercial copying
or commercial use of the code is not permitted without prior written permission.
See `LICENSE.md`.
