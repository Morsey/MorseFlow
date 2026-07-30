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

