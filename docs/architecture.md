# MorseFlow Architecture

MorseFlow separates room logic from local hardware control.

## Responsibilities

Node-RED:

- Owns puzzle, room, and game-state logic.
- Publishes commands to Morseboards over MQTT.
- Subscribes to board status, prop input, and presence topics.
- Decides how prop events affect the game.

MQTT broker:

- Provides wired message transport between Node-RED and all Morseboards.
- Tracks board online/offline state using retained status messages and Last Will and Testament.

Morseboard firmware:

- Owns local IO safety.
- Manages switched 5V prop power.
- Runs timed pulses without blocking.
- Sends simple audio commands to the DFPlayer Mini.
- Publishes board and prop status.
- Reconnects indefinitely after network or broker failures.
- Re-subscribes and republishes status after reconnect.

Prop Interface Boards:

- Convert RJ45 port power/signals into prop-specific hardware behavior.
- May be passive/simple boards or smart RP2040 Zero-class boards.
- Should prefer simple two-line status outputs where possible.

Standalone controllers:

- Handle focused hardware that does not connect through a Morseboard prop port.
- May expose a small local HTTP API when direct LAN control is useful.
- Must retain local physical control when their network is unavailable.

## Network Model

Morseboards are wired Ethernet devices; Wi-Fi remains intentionally out of
scope for the shared Morseboard runtime. Standalone controllers such as the
Pico W Temple Display may use Wi-Fi for their own local control API.
Use W5500-enabled MicroPython firmware matched to the exact board:

- WIZnet W5500-EVB-Pico for Pico 1.
- WIZnet W5500-EVB-Pico2 for Pico 2.

## Runtime Principles

- Firmware loops must remain responsive.
- Prop actions must not use blocking sleeps.
- Timed actions use `time.ticks_ms()` and scheduled/state-machine updates.
- All outputs should return to safe defaults after boot, disconnect, or errors.
- The board should continue retrying network and MQTT reconnects indefinitely.

