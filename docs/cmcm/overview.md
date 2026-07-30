# The Curse of Mount Clifton Manor

Short code: `CMCM`

MQTT room slug: `cmcm`

CMCM is the first real MorseFlow room and should drive firmware, MQTT, and prop
integration decisions until a second room proves what needs to be generalized.

## Implementation Rule

Build against the real CMCM room first:

- document actual boards as they are assigned;
- document actual prop ports as they are wired;
- document actual MQTT topics as Node-RED consumes them;
- keep production Node-RED flows outside this repository;
- generalize later only when real reuse appears.

## Topic Root

```text
morseflow/<site>/cmcm/<board_id>
```

Current default development board:

```text
morseflow/prodigy/cmcm/mb-001
```

