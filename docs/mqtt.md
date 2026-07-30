# MQTT Topic Convention

Default topic root:

```text
morseflow/<site>/<room>/<board_id>
```

Example:

```text
morseflow/prodigy/cmcm/mb-001/status
```

For the first MorseFlow room, **The Curse of Mount Clifton Manor** (`CMCM`),
use `cmcm` as the suggested room slug:

```text
morseflow/<site>/cmcm/<board_id>
```

## Board Status

| Topic | Direction | Retained | Purpose |
| --- | --- | --- | --- |
| `.../status` | MB to broker | yes | Online/offline availability and board metadata. |
| `.../state` | MB to broker | yes | Current local hardware state. |
| `.../event` | MB to broker | no | Edge/input events from ports or PIBs. |

The firmware should publish an MQTT Last Will and Testament to `.../status`
with an offline payload. After reconnect, it should republish online status,
current state, and re-subscribe to commands.

## Commands

| Topic | Direction | Purpose |
| --- | --- | --- |
| `.../cmd/power` | Node-RED to MB | Enable/disable switched 5V prop power. |
| `.../cmd/relay` | Node-RED to MB | Control optional onboard relay. |
| `.../cmd/port/<n>` | Node-RED to MB | Set or pulse port Signal A/B. |
| `.../cmd/audio` | Node-RED to MB | Send DFPlayer commands. |
| `.../cmd/status` | Node-RED to MB | Request immediate state/status publish. |

## Example Payloads

Enable switched 5V:

```json
{"enabled": true}
```

Pulse port 1 Signal A for 500 ms:

```json
{"a": {"pulse_ms": 500}}
```

Set port 4 Signal B high:

```json
{"b": true}
```

Play DFPlayer track 7:

```json
{"play_track": 7}
```
