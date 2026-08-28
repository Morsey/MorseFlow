# CMCM Board Status Log

Use this log for field status notes after upload or bench testing. Record the
software commit and whether local uncommitted changes were included.

## 2026-08-28

### mb-007

- Status: prepared for upload / current active board config.
- Reported by: bench/operator context.
- Hardware: W5500-EVB-Pico/Pico2 Morseboard.
- Role: candles on ports 1-3.
- Active config prepared: `firmware/morseboard/board_configs/mb_007.py` copied
  to `firmware/morseboard/board_config.py`.
- MQTT topic root: `morseflow/prodigy/cmcm/mb-007`.
- Test mode: MQTT disabled for no-network bench testing.
- Notes: candle hardware matches MB-001 candle ports; Signal A drives the candle
  LED output and Signal B reads the IR lit-detected input. Each configured LED
  lights for 5 seconds at power-up. One IR trigger turns the matching LED on
  for 5 seconds. In this no-network test mode, active IR level triggers are
  accepted without requiring a clean idle-to-active edge. MQTT disabled also
  stops the firmware from starting Ethernet or searching for the network.

### mb-002

- Status: ports 6 and 7 are broken.
- Reported by: bench/operator context.
- Hardware: W5500-EVB-Pico/Pico2 Morseboard.
- Impact: logical demon knockers/LEDs 4 and 5 were mapped to physical ports 6
  and 7, so those outputs should be treated as unavailable on this board until
  moved or repaired.
- MQTT topic root: `morseflow/prodigy/cmcm/mb-002`.

## 2026-08-22 14:36 BST

### mb-001

- Status: prepared for upload / current active board.
- Reported by: bench/operator context.
- Hardware: W5500-EVB-Pico/Pico2 Morseboard.
- Role: candles on ports 1-2; demon seal RFID readers on ports 3-7.
- Active config prepared: `firmware/morseboard/board_configs/mb_001.py` copied
  to `firmware/morseboard/board_config.py`.
- MQTT topic root: `morseflow/prodigy/cmcm/mb-001`.
- Firmware version: git commit `602a462`.
- Runtime start: `boot.py` auto-runs `app.main()`.
- Notes: RFID state changes are published immediately on
  `morseflow/prodigy/cmcm/mb-001/event`; events are live-only and not retained.

## 2026-08-22 14:28 BST

### mb-002

- Status: working.
- Reported by: bench/operator test.
- Hardware: W5500-EVB-Pico/Pico2 Morseboard.
- Role: demon knockers on ports 1-5.
- Active config uploaded: `firmware/morseboard/board_configs/mb_002.py` copied
  to `firmware/morseboard/board_config.py`.
- MQTT topic root: `morseflow/prodigy/cmcm/mb-002`.
- Firmware version: git commit `70e09d1` plus local uncommitted working-tree
  changes.
- Runtime start: `boot.py` auto-runs `app.main()`.
- Observed behavior: LED/knocker MQTT commands working.
- Related Node-RED flow: `node-red/flows/rfid-reader1-to-knocker1.json`.
- Notes: `PROP_5V_ENABLED_AT_BOOT = True`; switched prop 5V comes on at boot.
