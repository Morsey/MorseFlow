# CMCM Test Plan

Use this checklist as each board and prop is brought online.

## Board Bring-Up

- Board boots with all prop signals low.
- Switched 5V is off at boot.
- Optional relay is off at boot.
- USB REPL remains available during development.
- App reports network connected with assigned IP.
- MQTT does not start until the network is ready.
- Board publishes retained `status` online payload.
- Board publishes retained `state` payload.
- Last Will publishes offline status when the board disappears.

## Port Test

For each assigned port:

- Signal A can be set high and low.
- Signal B can be set high and low.
- Signal A timed pulse returns low without blocking firmware.
- Signal B timed pulse returns low without blocking firmware.
- Safe defaults return the prop to a safe state after reboot.

## Audio Test

- DFPlayer receives volume command.
- DFPlayer plays a known track.
- DFPlayer stops playback.

## Node-RED Integration

Production Node-RED flows are kept outside this repository. For each prop,
record the expected topics and payloads in `props.md` and `mqtt-topics.md`.

