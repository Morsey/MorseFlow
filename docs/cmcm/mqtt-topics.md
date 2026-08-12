# CMCM MQTT Topics

CMCM uses:

```text
morseflow/<site>/cmcm/<board_id>
```

Current development root:

```text
morseflow/prodigy/cmcm/mb-001
```

## Board Topics

| Purpose | Topic |
| --- | --- |
| Availability | `morseflow/prodigy/cmcm/mb-001/status` |
| Retained hardware state | `morseflow/prodigy/cmcm/mb-001/state` |
| Prop/input events | `morseflow/prodigy/cmcm/mb-001/event` |
| Switched 5V command | `morseflow/prodigy/cmcm/mb-001/cmd/power` |
| Relay command | `morseflow/prodigy/cmcm/mb-001/cmd/relay` |
| Audio command | `morseflow/prodigy/cmcm/mb-001/cmd/audio` |
| Status request | `morseflow/prodigy/cmcm/mb-001/cmd/status` |
| Port command | `morseflow/prodigy/cmcm/mb-001/cmd/port/<n>` |

Switched 5V prop power is normally on from boot. Use `cmd/power` mainly to
reset or recover attached PIBs.

## RFID Input Events

For RFID PIB input ports, the Morseboard publishes state changes to:

```text
morseflow/prodigy/cmcm/mb-001/event
```

Example demon-seal reader event. The changed reader is reported at the top
level, and `readers` carries the current status of all demon-seal RFID readers:

```json
{"board_id": "mb-001", "event": "rfid", "data": {"port": 3, "rfid": "correct", "previous": "no_card", "prop": "demon_seal_1", "reader": 1, "readers": [{"port": 3, "rfid": "correct", "prop": "demon_seal_1", "reader": 1}, {"port": 4, "rfid": "wrong", "prop": "demon_seal_2", "reader": 2}], "all_correct": false}}
```

RFID states are:

- `no_card`
- `correct`
- `wrong`
- `invalid` when both status lines are high

For MB1 ports 3-7, Signal A is currently mapped as wrong-card input and Signal B
as correct-card input.

The retained board `state` payload also includes:

```json
{"demon_seals": {"readers": [{"port": 3, "rfid": "correct", "prop": "demon_seal_1", "reader": 1}], "all_correct": false}}
```

## Example Commands

Pulse port 1 Signal A:

```json
{"a": {"pulse_ms": 500}}
```

Set port 1 Signal B high:

```json
{"b": true}
```

Play DFPlayer track 1:

```json
{"play_track": 1}
```
