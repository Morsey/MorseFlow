# CMCM Board Status Log

Use this log for field status notes after upload or bench testing. Record the
software commit and whether local uncommitted changes were included.

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
