# CMCM Prop Port Map

Record real prop wiring here. Node-RED owns game logic; this table documents
what each Morseboard port physically controls or reports.

## MB-001

The candle outputs on ports 1-2 start off and are controlled over MQTT. Their
IR input changes publish candle events without switching the outputs locally.
The RFID behavior on ports 3-7 is unchanged.

| Port | Signal A | Signal B | Prop Power | Prop / PIB | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Candle LED output | IR lit-detected input | Switched 5V normally on, 12V always live | Candle 1 | Bench test |
| 2 | Candle LED output | IR lit-detected input | Switched 5V normally on, 12V always live | Candle 2 | Bench test |
| 3 | RFID wrong-card input | RFID correct-card input | Switched 5V normally on, 12V always live | Demon seals RFID reader 1 | Bench test |
| 4 | RFID wrong-card input | RFID correct-card input | Switched 5V normally on, 12V always live | Demon seals RFID reader 2 | Bench test |
| 5 | RFID wrong-card input | RFID correct-card input | Switched 5V normally on, 12V always live | Demon seals RFID reader 3 | Bench test |
| 6 | RFID wrong-card input | RFID correct-card input | Switched 5V normally on, 12V always live | Demon seals RFID reader 4 | Bench test |
| 7 | RFID wrong-card input | RFID correct-card input | Switched 5V normally on, 12V always live | Demon seals RFID reader 5 | Bench test |
| 8 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |

## MB-002

Ports 1-3 and 6-7 are working direct-wired demon knocker props with no PIB
microcontroller. Physical ports 4 and 5 are broken and must not be used. Signal
A drives each solenoid output. Signal B drives each NeoPixel data line directly
from the Morseboard.

| Port | Signal A | Signal B | Prop Power | Prop / PIB | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 1, no PIB firmware | Bench test |
| 2 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 2, no PIB firmware | Bench test |
| 3 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 3, no PIB firmware | Bench test |
| 4 | Unavailable | Unavailable | Do not use | None | Broken port |
| 5 | Unavailable | Unavailable | Do not use | None | Broken port |
| 6 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 4, no PIB firmware | Bench test |
| 7 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 5, no PIB firmware | Bench test |
| 8 | Cross-drop solenoid output | Active-low reed-switch input | Switched 5V normally on, 12V always live | Cross drop | Configured |

## MB-003

MB-003 reads the four Beasts RFID PIBs, drives three latch locks, and reads two
active-low puzzle switches. Latch commands are safety-capped by firmware.

| Port | Signal A | Signal B | Prop Power | Prop / PIB | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | RFID wrong-tag input | RFID correct-tag input | Switched 5V normally on, 12V always live | Beasts reader 1 | Configured |
| 2 | RFID wrong-tag input | RFID correct-tag input | Switched 5V normally on, 12V always live | Beasts reader 2 | Configured |
| 3 | RFID wrong-tag input | RFID correct-tag input | Switched 5V normally on, 12V always live | Beasts reader 3 | Configured |
| 4 | RFID wrong-tag input | RFID correct-tag input | Switched 5V normally on, 12V always live | Beasts reader 4 | Configured |
| 5 | Latch lock 2 | Latch lock 13 | Switched 5V normally on, 12V always live | Latch locks | Configured |
| 6 | Latch lock 12 | Unused | Switched 5V normally on, 12V always live | Latch lock | Configured |
| 7 | Pull-cord input | Vampire-delay input | Switched 5V normally on, 12V always live | Puzzle switches | Configured |
| 8 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | None | Open |

## MB-004

MB-004 drives a 12-pixel blue NeoPixel chase from port 1 Signal A. Signal B is
unused and held low.

## MB-007

Ports 1-3 use the same candle hardware pattern as MB-001. Signal A drives the
candle LED output. Signal B reads the IR lit-detected input. Outputs start off
and do not respond locally to the IR sensors. IR state changes are published as
MQTT candle events, and Node-RED controls each output through its port command
topic.

| Port | Signal A | Signal B | Prop Power | Prop / PIB | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Candle LED output | IR lit-detected input | Switched 5V normally on, 12V always live | Candle 1 | Configured |
| 2 | Candle LED output | IR lit-detected input | Switched 5V normally on, 12V always live | Candle 2 | Configured |
| 3 | Candle LED output | IR lit-detected input | Switched 5V normally on, 12V always live | Candle 3 | Configured |
| 4 | I2C0 SDA | I2C0 SCL | Switched 5V normally on, 12V always live | BCDoor VL53L0X | Configured |
| 5 | Latch lock 1 | Unused | Switched 5V normally on, 12V always live | Latch-lock controller | Configured |
| 6 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |
| 7 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |
| 8 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |

## MB-006

The bookshelf uses direct GPIO wiring rather than the normal paired RJ45 port
abstraction. Books 1-5 occupy shelf 1 and Books 6-10 occupy shelf 2.

| GPIO | Matrix role | Books |
| --- | --- | --- |
| 0-4 | Shared book columns, physically reversed | 5/10, 4/9, 3/8, 2/7, 1/6 |
| 5 | Shelf 1 out row | 1-5 |
| 6 | Shelf 1 in row | 1-5 |
| 7 | Shelf 2 out row | 6-10 |
| 8 | Shelf 2 in row | 6-10 |
| 10 | AS5600 I2C1 SDA | Doorknob safe dial |
| 11 | AS5600 I2C1 SCL | Doorknob safe dial |

The doorknob sequence is checked on MB-006 itself. A successful combination is
reported through MQTT; it does not operate the optional relay.

## MB-010

Ports 5-7 are RFID PIBs for the Hang the Dolls puzzle. Signal A reports a
wrong tag and Signal B reports the correct tag. The DFPlayer Mini uses its
dedicated UART pins and does not consume an RJ45 port.

| Port | Signal A | Signal B | Prop Power | Prop / PIB | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | I2C1 SDA | I2C1 SCL | Switched 5V normally on, 12V always live | TOF1 VL53L0X | Configured |
| 2 | I2C0 SDA | I2C0 SCL | Switched 5V normally on, 12V always live | TOF2 VL53L0X | Configured |
| 3 | Latch lock 1 | Latch lock 2 | Switched 5V normally on, 12V always live | Latch-lock controllers | Configured |
| 4 | Generic output | Generic output | Switched 5V normally on, 12V always live | None | Open |
| 5 | RFID wrong-tag input | RFID correct-tag input | Switched 5V normally on, 12V always live | Doll 1 RFID reader | Bench tested |
| 6 | RFID wrong-tag input | RFID correct-tag input | Switched 5V normally on, 12V always live | Doll 2 RFID reader | Bench tested |
| 7 | RFID wrong-tag input | RFID correct-tag input | Switched 5V normally on, 12V always live | Doll 3 RFID reader | Bench tested |
| 8 | Unused | Reed-switch input, active-low with pull-up | GND used by dry contact; prop power not required | Cross on Symbols sensor 2 | Configured |

## Prop Template

```text
Prop name:
Board ID:
Port:
Signal A function:
Signal B function:
Uses switched 5V:
Uses always-live 12V:
PIB type:
Node-RED topic(s):
Safe default:
Test notes:
```
