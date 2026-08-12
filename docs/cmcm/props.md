# CMCM Prop Port Map

Record real prop wiring here. Node-RED owns game logic; this table documents
what each Morseboard port physically controls or reports.

## MB-001

| Port | Signal A | Signal B | Prop Power | Prop / PIB | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |
| 2 | Unassigned | Unassigned | Switched 5V normally on, 12V always live | TBD | Open |
| 3 | RFID wrong-card input | RFID correct-card input | Switched 5V normally on, 12V always live | Demon seals RFID reader 1 | Bench test |
| 4 | RFID wrong-card input | RFID correct-card input | Switched 5V normally on, 12V always live | Demon seals RFID reader 2 | Bench test |
| 5 | RFID wrong-card input | RFID correct-card input | Switched 5V normally on, 12V always live | Demon seals RFID reader 3 | Bench test |
| 6 | RFID wrong-card input | RFID correct-card input | Switched 5V normally on, 12V always live | Demon seals RFID reader 4 | Bench test |
| 7 | RFID wrong-card input | RFID correct-card input | Switched 5V normally on, 12V always live | Demon seals RFID reader 5 | Bench test |
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
