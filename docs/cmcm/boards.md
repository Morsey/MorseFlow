# CMCM Morseboards

Record each physical Morseboard here as it is installed or tested. For dated
test/upload notes, see `docs/cmcm/board-status-log.md`.

| Board ID | Config | Hardware | Location | IP Mode | MQTT Topic Root | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `mb-001` | `firmware/morseboard/board_configs/mb_001.py` | W5500-EVB-Pico/Pico2 | Bench/dev | DHCP | `morseflow/prodigy/cmcm/mb-001` | Candles on ports 1-2; demon seals RFID readers on ports 3-7. |
| `mb-002` | `firmware/morseboard/board_configs/mb_002.py` | W5500-EVB-Pico/Pico2 | Bench/dev | DHCP | `morseflow/prodigy/cmcm/mb-002` | Demon knockers on ports 1-3 and 6-7. |
| `mb-003` | `firmware/morseboard/board_configs/mb_003.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-003` | Reserved. |
| `mb-004` | `firmware/morseboard/board_configs/mb_004.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-004` | Reserved. |
| `mb-005` | `firmware/morseboard/board_configs/mb_005.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-005` | Reserved. |
| `mb-006` | `firmware/morseboard/board_configs/mb_006.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-006` | Reserved. |
| `mb-007` | `firmware/morseboard/board_configs/mb_007.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-007` | Reserved. |
| `mb-008` | `firmware/morseboard/board_configs/mb_008.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-008` | Reserved. |
| `mb-009` | `firmware/morseboard/board_configs/mb_009.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-009` | Reserved. |
| `mb-010` | `firmware/morseboard/board_configs/mb_010.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-010` | Reserved. |

## Connected Props

### MB-001

MB-001 is the demon seals input board plus the first two candle inputs/outputs.
Its active config is `firmware/morseboard/board_configs/mb_001.py`.

| Port | Connected prop | Signal A | Signal B | MQTT role |
| --- | --- | --- | --- | --- |
| 1 | Candle 1 | Candle LED output | IR lit-detected input | `candle_1` |
| 2 | Candle 2 | Candle LED output | IR lit-detected input | `candle_2` |
| 3 | Demon seal RFID reader 1 | Wrong-card input | Correct-card input | `demon_seal_1` / reader 1 |
| 4 | Demon seal RFID reader 2 | Wrong-card input | Correct-card input | `demon_seal_2` / reader 2 |
| 5 | Demon seal RFID reader 3 | Wrong-card input | Correct-card input | `demon_seal_3` / reader 3 |
| 6 | Demon seal RFID reader 4 | Wrong-card input | Correct-card input | `demon_seal_4` / reader 4 |
| 7 | Demon seal RFID reader 5 | Wrong-card input | Correct-card input | `demon_seal_5` / reader 5 |
| 8 | Not connected | Unassigned | Unassigned | Open |

For the RFID PIB wiring on MB-001, Signal A reports wrong-card and Signal B
reports correct-card.

### MB-002

MB-002 is the demon knocker output board. Its active config is
`firmware/morseboard/board_configs/mb_002.py`.

| Port | Connected prop | Signal A | Signal B | MQTT role | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | Demon knocker 1 | Solenoid output | NeoPixel data output | `demon_knocker_1` / knocker 1 / LED 1 | RGB pixel order |
| 2 | Demon knocker 2 | Solenoid output | NeoPixel data output | `demon_knocker_2` / knocker 2 / LED 2 | RGB pixel order |
| 3 | Demon knocker 3 | Solenoid output | NeoPixel data output | `demon_knocker_3` / knocker 3 / LED 3 | RGB pixel order |
| 4 | Not connected | Generic output | Generic output | Open | Reserved |
| 5 | Not connected | Generic output | Generic output | Open | Reserved |
| 6 | Demon knocker 4 | Solenoid output | NeoPixel data output | `demon_knocker_4` / knocker 4 / LED 4 | GRB pixel order correction |
| 7 | Demon knocker 5 | Solenoid output | NeoPixel data output | `demon_knocker_5` / knocker 5 / LED 5 | GRB pixel order correction |
| 8 | Not connected | Generic output | Generic output | Open | Reserved |

Use the logical MQTT targets `cmd/demon_knocker/<1-5>` and
`cmd/demon_led/<1-5>` from Node-RED. The firmware maps those logical numbers to
the physical ports above, so Node-RED does not need to know that knockers 4 and
5 are on ports 6 and 7 or that LEDs 4 and 5 use GRB colour order.

### MB-003 To MB-010

These boards are reserved. No connected props are currently recorded in their
board config files.

## Board Template

```text
Board ID:
Config file:
Hardware:
Physical location:
Firmware version/commit:
IP address or DHCP reservation:
MQTT topic root:
Connected props/ports:
DFPlayer fitted:
Onboard relay fitted:
Notes:
```
