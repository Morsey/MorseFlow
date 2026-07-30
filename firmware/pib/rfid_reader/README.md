# RFID Prop Interface Board

This folder is a starter for smart RFID PIB firmware.

Default design goal:

- Keep the Morseboard-facing interface simple.
- Report only the state Node-RED normally needs:
  - no card
  - correct card present
  - incorrect card present
- Use serial card-ID reporting only when the room logic truly needs the actual ID.

## Suggested Signal Use

For a simple two-line status output to a Morseboard prop port:

- Signal A: correct card present.
- Signal B: incorrect card present.
- Both low: no card.

The Morseboard can then publish these as normal prop input states or events.

## PN5180 Note

PN5180 support depends on the exact MicroPython driver/library chosen for the
smart PIB board. `main.py` contains a polling/state-machine skeleton and a
placeholder `read_card_id()` function where the PN5180 integration belongs.

