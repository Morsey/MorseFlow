# CMCM Prop Port Map

Record real prop wiring here. Node-RED owns game logic; this table documents
what each Morseboard port physically controls or reports.

## MB-001

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

Ports 1-5 are direct-wired demon knocker props with no PIB microcontroller.
Signal A drives each solenoid output. Signal B drives each NeoPixel data line
directly from the Morseboard.

| Port | Signal A | Signal B | Prop Power | Prop / PIB | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 1, no PIB firmware | Bench test |
| 2 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 2, no PIB firmware | Bench test |
| 3 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 3, no PIB firmware | Bench test |
| 4 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 4, no PIB firmware | Bench test |
| 5 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 5, no PIB firmware | Bench test |
| 6 | Generic output | Generic output | Switched 5V normally on, 12V always live | None | Open |
| 7 | Generic output | Generic output | Switched 5V normally on, 12V always live | None | Open |
| 8 | Generic output | Generic output | Switched 5V normally on, 12V always live | None | Open |

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
