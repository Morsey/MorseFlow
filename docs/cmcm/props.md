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

Ports 1-3 are working direct-wired demon knocker props with no PIB
microcontroller. Ports 6 and 7 were wired for demon knockers 4 and 5 but are
currently broken and should not be relied on. Signal A drives each solenoid
output. Signal B drives each NeoPixel data line directly from the Morseboard.

| Port | Signal A | Signal B | Prop Power | Prop / PIB | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 1, no PIB firmware | Bench test |
| 2 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 2, no PIB firmware | Bench test |
| 3 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 3, no PIB firmware | Bench test |
| 4 | Generic output | Generic output | Switched 5V normally on, 12V always live | None | Open |
| 5 | Generic output | Generic output | Switched 5V normally on, 12V always live | None | Open |
| 6 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 4, no PIB firmware | Broken port |
| 7 | Solenoid output | NeoPixel data output | Switched 5V normally on, 12V always live | Demon knocker 5, no PIB firmware | Broken port |
| 8 | Generic output | Generic output | Switched 5V normally on, 12V always live | None | Open |

## MB-007

Ports 1-3 use the same candle hardware pattern as MB-001. Signal A drives the
candle LED output. Signal B reads the IR lit-detected input. For the current
no-network test, each LED lights for 5 seconds at power-up, and one IR
trigger turns the matching candle LED on for 5 seconds. An active IR input is
enough to trigger the LED in this test mode; it does not require a clean
idle-to-active edge. MQTT is disabled, so the firmware does not start Ethernet
or search for the network.

| Port | Signal A | Signal B | Prop Power | Prop / PIB | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Candle LED output | IR lit-detected input | Switched 5V normally on, 12V always live | Candle 1 | Configured |
| 2 | Candle LED output | IR lit-detected input | Switched 5V normally on, 12V always live | Candle 2 | Configured |
| 3 | Candle LED output | IR lit-detected input | Switched 5V normally on, 12V always live | Candle 3 | Configured |
| 4 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |
| 5 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |
| 6 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |
| 7 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |
| 8 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |

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
