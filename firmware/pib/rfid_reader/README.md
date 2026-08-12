# RFID Prop Interface Board

This folder contains smart RFID PIB firmware for PN5180-based reader boards.

Default design goal:

- Keep the Morseboard-facing interface simple.
- Report only the state Node-RED normally needs:
  - no card
  - correct card present
  - wrong card present
- Keep card enrollment local to the RFID PIB.

## Suggested Signal Use

For a simple two-line status output to a Morseboard prop port:

- Signal A: correct card present.
- Signal B: wrong card present.
- Both low: no card.

The Morseboard can then publish these as normal prop input states or events.

## Hardware

PN5180 wiring is taken from the original CMCM reader-board reference firmware:

| Function | GPIO |
| --- | --- |
| PN5180 NSS | GPIO2 |
| PN5180 RST | GPIO1 |
| PN5180 BSY | GPIO3 |
| PN5180 SCK | GPIO10 |
| PN5180 MOSI | GPIO11 |
| PN5180 MISO | GPIO12 |
| NeoPixel | GPIO13 |
| Add card button | GPIO14 |
| Remove card button | GPIO29 |
| Correct-card output | GPIO26 |
| Wrong-card output | GPIO27 |

Buttons are configured as pull-ups and are expected to pull the GPIO low when
pressed.

## Card List

Correct card IDs are stored on the PIB filesystem in `correct_cards.json`.

- Press ADD while a card is present to add that card to the correct list.
- Press Remove while a card is present to remove that card from the correct list.
- Press ADD and Remove together to clear the stored list.

`config.DEFAULT_CORRECT_CARD_IDS` is used only when no stored card file exists.
After the first add, remove, or clear action, `correct_cards.json` becomes the
source of truth.

The firmware filters occasional bad PN5180 reads before changing state or
learning a card. UIDs with invalid lengths are ignored, and a new UID must be
read `config.CARD_STABLE_READS` times in a row before it is accepted.

## Board Files

Upload these files together to the RFID PIB:

- `main.py`
- `config.py`
- `pn5180_morse.py`
