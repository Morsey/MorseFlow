# MQTT Payload Examples

Assume board topic root:

```text
morseflow/prodigy/cmcm/mb-001
```

## Power

```text
Topic: morseflow/prodigy/cmcm/mb-001/cmd/power
Payload: {"enabled": true}
```

## Timed Prop Pulse

```text
Topic: morseflow/prodigy/cmcm/mb-001/cmd/port/1
Payload: {"a": {"pulse_ms": 500}, "b": false}
```

## Audio

```text
Topic: morseflow/prodigy/cmcm/mb-001/cmd/audio
Payload: {"play_track": 3}
```

## Status Request

```text
Topic: morseflow/prodigy/cmcm/mb-001/cmd/status
Payload: {}
```
