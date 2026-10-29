# CMCM Morseboards

Record each physical Morseboard here as it is installed or tested. For dated
test/upload notes, see `docs/cmcm/board-status-log.md`.

| Board ID | Config | Hardware | Location | IP Mode | MQTT Topic Root | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `mb-001` | `firmware/morseboard/board_configs/mb_001.py` | W5500-EVB-Pico/Pico2 | Bench/dev | DHCP | `morseflow/prodigy/cmcm/mb-001` | MQTT-controlled candles on ports 1-2; demon seals RFID readers on ports 3-7. |
| `mb-002` | `firmware/morseboard/board_configs/mb_002.py` | W5500-EVB-Pico/Pico2 | Bench/dev | DHCP | `morseflow/prodigy/cmcm/mb-002` | Demon knockers on ports 1-3 and 6-7; cross drop on port 8; ports 4 and 5 are broken. |
| `mb-003` | `firmware/morseboard/board_configs/mb_003.py` | W5500-EVB-Pico/Pico2 | Bench/dev | DHCP | `morseflow/prodigy/cmcm/mb-003` | Beasts RFID readers on ports 1-4; latch locks on ports 5-6; pull cord and vampire delay switch on port 7. |
| `mb-004` | `firmware/morseboard/board_configs/mb_004.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-004` | Reserved. |
| `mb-005` | `firmware/morseboard/board_configs/mb_005.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-005` | Reserved. |
| `mb-006` | `firmware/morseboard/board_configs/mb_006.py` | Special screw-terminal W5500-EVB-Pico/Pico2 | Installed/networked | DHCP | `morseflow/prodigy/cmcm/mb-006` | Bookshelf on GPIO0-GPIO8; AS5600 safe dial on GPIO10/GPIO11. |
| `mb-007` | `firmware/morseboard/board_configs/mb_007.py` | W5500-EVB-Pico/Pico2 | Bench/dev | DHCP | `morseflow/prodigy/cmcm/mb-007` | Candles on ports 1-3; IR changes publish over MQTT; outputs are controlled over MQTT. |
| `mb-008` | `firmware/morseboard/board_configs/mb_008.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-008` | Reserved. |
| `mb-009` | `firmware/morseboard/board_configs/mb_009.py` | TBD | TBD | DHCP | `morseflow/prodigy/cmcm/mb-009` | Reserved. |
| `mb-010` | `firmware/morseboard/board_configs/mb_010.py` | W5500-EVB-Pico/Pico2 | Bench/dev | DHCP | `morseflow/prodigy/cmcm/mb-010` | DFPlayer Mini; direct ToF sensors on ports 1-2; Hang the Dolls RFID readers on ports 5-7; Cross on Symbols sensor 2 on port 8. |

## Connected Props

### MB-001

MB-001 is the demon seals input board plus the first two candle inputs/outputs.
Its active config is `firmware/morseboard/board_configs/mb_001.py`.
The candle outputs start off and are controlled over MQTT. Candle IR input
changes publish events but do not switch the outputs locally.

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
| 4 | Not connected | Unavailable | Unavailable | Open | Broken port; do not use |
| 5 | Not connected | Unavailable | Unavailable | Open | Broken port; do not use |
| 6 | Demon knocker 4 | Solenoid output | NeoPixel data output | `demon_knocker_4` / knocker 4 / LED 4 | GRB pixel order |
| 7 | Demon knocker 5 | Solenoid output | NeoPixel data output | `demon_knocker_5` / knocker 5 / LED 5 | GRB pixel order |
| 8 | Cross drop | Solenoid output | Reed-switch input | `cross_drop` | Signal A pulses the release; Signal B detects the cross |

Use the logical MQTT targets `cmd/demon_knocker/<1-5>` and
`cmd/demon_led/<1-5>` from Node-RED. The firmware maps those logical numbers to
the physical ports above. Physical ports 4 and 5 are broken and must not be
used; logical knockers/LEDs 4 and 5 are available through physical ports 6 and
7.

Drop the cross through `cmd/port/8` with `{"drop": true}`. The pulse defaults
to 500 ms and is capped at 1000 ms. Reed-switch changes are published as
normal `switch` events.

### MB-003

MB-003 reads the four Beasts RFID PIBs. Signal A reports a wrong tag and
Signal B reports the correct tag, following the existing RFID PIB wiring
convention.

| Port | Connected prop | Signal A | Signal B | MQTT role |
| --- | --- | --- | --- | --- |
| 1 | Beasts RFID reader 1 | Wrong-tag input | Correct-tag input | `beasts_1` / reader 1 |
| 2 | Beasts RFID reader 2 | Wrong-tag input | Correct-tag input | `beasts_2` / reader 2 |
| 3 | Beasts RFID reader 3 | Wrong-tag input | Correct-tag input | `beasts_3` / reader 3 |
| 4 | Beasts RFID reader 4 | Wrong-tag input | Correct-tag input | `beasts_4` / reader 4 |
| 5 | Latch locks | Lock 2, active-high pulse | Lock 13, active-high pulse | `latch_lock/2` and `latch_lock/13` |
| 6 | Latch lock | Lock 12, active-high pulse | Unused | `latch_lock/12` |
| 7 | Puzzle switches | Pull cord, active-low input | Vampire delay switch, active-low input | `pull_cord` and `vampire_delay_switch` |
| 8 | Not connected | Generic input/output | Generic input/output | Open |

Latch locks 2, 13, and 12 are opened through `cmd/latch_lock/2`,
`cmd/latch_lock/13`, and `cmd/latch_lock/12`. The default pulse is 100 ms, and
firmware clamps every requested duration to the configured 1,000 ms safety
limit.

The two port 7 inputs use internal pull-ups and 50 ms debounce. Their current
values appear in the retained board state's `switches` list. Changes publish a
live `switch` event containing the changed input and the status of both inputs.

### MB-007

MB-007 is a candle input/output board using the same candle hardware pattern as
MB-001. Its active config is `firmware/morseboard/board_configs/mb_007.py`.
MQTT is enabled. IR input changes publish candle events but do not switch the
matching candle output locally. Candle outputs start off and remain under MQTT
control until explicitly changed.

| Port | Connected prop | Signal A | Signal B | MQTT role |
| --- | --- | --- | --- | --- |
| 1 | Candle 1 | Candle LED output | IR lit-detected input | `candle_1` |
| 2 | Candle 2 | Candle LED output | IR lit-detected input | `candle_2` |
| 3 | Candle 3 | Candle LED output | IR lit-detected input | `candle_3` |
| 4 | Not connected | Unassigned | Unassigned | Open |
| 5 | Not connected | Unassigned | Unassigned | Open |
| 6 | Not connected | Unassigned | Unassigned | Open |
| 7 | Not connected | Unassigned | Unassigned | Open |
| 8 | Not connected | Unassigned | Unassigned | Open |

### MB-006

MB-006 reads the ten-book bookshelf directly as a 5-column by 4-row reed-switch
matrix. GPIO0-GPIO4 select the five positions shared between the shelves.
GPIO5/GPIO6 read the out/in positions for Books 1-5, and GPIO7/GPIO8 read the
out/in positions for Books 6-10. The scanner discharges the row circuitry
before each reading because the input board otherwise retains a high level
after a switch opens.

The physical book order is reversed across GPIO0-GPIO4. Those columns map to
Books 5/10, 4/9, 3/8, 2/7, and 1/6 respectively.

The bookshelf owns GPIO0-GPIO8, so Morseboard ports 1-3 and Signal A of port 4
are reserved on MB-006. The firmware reserves all of ports 1-4 to prevent
conflicting output initialization or commands. The DFPlayer is disabled because
the matrix uses its normal UART0 pins GPIO0/GPIO1.

MB-006 is the special screw-terminal Morseboard rather than the paired-port
version. An AS5600 magnetic angle sensor for the doorknob safe puzzle uses
I2C1 on GPIO10 SDA and GPIO11 SCL. The safe combination is monitored locally;
only progress, reset, unlock, configuration, and sensor-health events are sent
over MQTT. GPIO15 is left unclaimed because this board exposes it as a screw
terminal instead of using it as the normal switched-5V control.

### MB-010

MB-010 has a DFPlayer Mini connected to the board's dedicated UART0 pins:
GPIO0 to DFPlayer RX and GPIO1 from DFPlayer TX. It is controlled through
`morseflow/prodigy/cmcm/mb-010/cmd/audio`; play-track and immediate-stop
commands have been verified on the bench. The DFPlayer does not consume an
RJ45 prop port.

Ports 5-7 are the Hang the Dolls RFID readers. They use the same RFID PIB
wiring as MB-001: Signal A reports a wrong tag and Signal B reports the correct
tag. All three readers have been verified on the bench.

Port 8 is Cross on Symbols sensor 2, a dry-contact reed switch. Signal B uses
an internal pull-up and becomes active when the switch closes to GND. Signal A
is unused. Input changes are debounced for 50 ms and published over MQTT.

| Port | Connected prop | Signal A | Signal B | MQTT role |
| --- | --- | --- | --- | --- |
| 1 | TOF1 (VL53L0X) | I2C1 SDA | I2C1 SCL | `tof_1` / `TOF1` |
| 2 | TOF2 (VL53L0X) | I2C0 SDA | I2C0 SCL | `tof_2` / `TOF2` |
| 3-4 | Not connected | Generic input/output | Generic input/output | Open |
| 5 | Doll 1 RFID reader | Wrong-tag input | Correct-tag input | `doll_1` / reader 1 |
| 6 | Doll 2 RFID reader | Wrong-tag input | Correct-tag input | `doll_2` / reader 2 |
| 7 | Doll 3 RFID reader | Wrong-tag input | Correct-tag input | `doll_3` / reader 3 |
| 8 | Cross on Symbols sensor 2 | Unused | Reed-switch input, active-low | `cross_on_symbols_2` / sensor 2 |

### MB-003 To MB-005 And MB-008 To MB-009

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
