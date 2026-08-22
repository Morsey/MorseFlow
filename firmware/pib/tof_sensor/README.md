# ToF Prop Interface Board

This folder contains starter bring-up code for a Pico-class PIB using a
VL53L0X/VL53L1X-style time-of-flight distance sensor.

## Design Goal

The ToF sensor runs locally on the PIB over I2C. The Morseboard does not talk to
the ToF sensor directly. It only reads simple PIB status outputs over one RJ45
prop port.

## Suggested Signal Use

For a simple two-line status output to a Morseboard prop port:

- Signal A: object near / threshold active.
- Signal B: sensor healthy / object far.
- Both low: idle or not ready.
- Both high: sensor error.

## Default PIB Wiring

| Function | GPIO |
| --- | --- |
| ToF SDA | GPIO4 |
| ToF SCL | GPIO5 |
| Near output to Morseboard Signal A | GPIO26 |
| Far output to Morseboard Signal B | GPIO27 |

Most VL53 breakout boards use I2C address `0x29`. Confirm the breakout power
requirements before connecting VCC. Many modules accept 3V3 only; some breakout
boards include regulation and level shifting for 5V.

## Bring-Up Test

Upload these files to the ToF PIB:

- `config.py`
- `test_scripts/tof_i2c_test.py` copied to the device root as `tof_i2c_test.py`

From the REPL:

```python
import tof_i2c_test
tof_i2c_test.main()
```

The test pulses both Morseboard-facing outputs, scans the local I2C bus, and
prints whether a ToF sensor responds at `0x29`.

## Range Test

For VL53L0X distance readings, upload:

- `config.py`
- `test_scripts/tof_range_test.py` copied to the device root as `tof_range_test.py`
- `vl53l0x.py`

From the REPL:

```python
import tof_range_test
tof_range_test.main()
```

The script prints the range in millimeters every `config.RANGE_INTERVAL_MS` and
drives the near/far outputs using `config.NEAR_THRESHOLD_MM`.
