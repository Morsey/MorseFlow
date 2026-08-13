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
| Knock sequence command | `morseflow/prodigy/cmcm/mb-001/cmd/sequence` |
| Status request | `morseflow/prodigy/cmcm/mb-001/cmd/status` |
| Port command | `morseflow/prodigy/cmcm/mb-001/cmd/port/<n>` |

Switched 5V prop power is normally on from boot. Use `cmd/power` mainly to
reset or recover attached PIBs.

The retained `status` payload is also refreshed every `STATUS_INTERVAL_MS` and
includes board uptime in milliseconds:

```json
{"status": "online", "board_id": "mb-001", "firmware": "morseboard-skeleton", "ip": "192.168.10.51", "uptime_ms": 123456}
```

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

## Candle Events

MB1 ports 1 and 2 are passive candle PIBs. Signal A drives the candle LED.
Signal B reads the active-low IR lit-detected signal.

When a candle sensor triggers, the Morseboard turns that candle output on for
`CANDLE_ON_TIME_MS` and publishes:

```text
morseflow/prodigy/cmcm/mb-001/event
```

Example candle event:

```json
{"board_id": "mb-001", "event": "candle", "data": {"port": 1, "candle_on": true, "sensor_active": true, "prop": "candle_1", "candle": 1, "armed_for_trigger": false, "candles": [{"port": 1, "candle_on": true, "sensor_active": true, "prop": "candle_1", "candle": 1}, {"port": 2, "candle_on": false, "sensor_active": false, "prop": "candle_2", "candle": 2}]}}
```

The retained board `state` payload includes a top-level `candles` list with the
current state of all configured candle ports.

## Demon Knocker Commands

MB2 ports 1-5 are direct-wired demon knockers. Signal A drives each solenoid,
and Signal B drives each NeoPixel data line.

Pulse the knocker for the default `DEMON_KNOCKER_PULSE_MS`:

```json
{"knock": true}
```

Pulse the knocker for a specific duration:

```json
{"knock_ms": 120}
```

Set the NeoPixel:

```json
{"pixel": [255, 0, 0]}
```

Turn the prop outputs off:

```json
{"off": true}
```

## Demon Knocker Sequences

Send a board-level sequence command to:

```text
morseflow/prodigy/cmcm/mb-002/cmd/sequence
```

The sequence runs without blocking MQTT. Steps run in order. Use `knocker` to
target demon knocker 1-5. `port` is still accepted as a compatibility alias.
Within each step, `pulses` can define uneven knock timings. Each pulse can set
`knock_ms`, `pause_ms`, `pixel`, and `pixel_pulse`. `pause_ms` is the delay
after that pulse before the next pulse in the same step. `after_ms` is the delay
before the next knocker step. When `pixel_pulse` is true, the NeoPixel is set to
`pixel` during the knock and turned off during the pause.

```json
{
  "steps": [
    {
      "knocker": 1,
      "after_ms": 300,
      "pulses": [
        {"knock_ms": 100, "pause_ms": 90, "pixel": [255, 0, 0], "pixel_pulse": true},
        {"knock_ms": 160, "pause_ms": 240, "pixel": [255, 0, 0], "pixel_pulse": true},
        {"knock_ms": 80, "pause_ms": 0, "pixel": [255, 0, 0], "pixel_pulse": true}
      ]
    },
    {
      "knocker": 2,
      "after_ms": 300,
      "pulses": [
        {"knock_ms": 120, "pause_ms": 140, "pixel": [255, 80, 0], "pixel_pulse": true},
        {"knock_ms": 120, "pause_ms": 0, "pixel": [255, 80, 0], "pixel_pulse": true}
      ]
    }
  ]
}
```

For evenly spaced knocks, the shorter form is still supported:

```json
{
  "steps": [
    {"knocker": 1, "knocks": 3, "knock_ms": 120, "pause_ms": 180, "after_ms": 300, "pixel": [255, 0, 0], "pixel_pulse": true},
    {"knocker": 2, "knocks": 2, "knock_ms": 120, "pause_ms": 180, "after_ms": 0, "pixel": [255, 80, 0], "pixel_pulse": true}
  ]
}
```

Stop the current sequence:

```json
{"stop": true}
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
