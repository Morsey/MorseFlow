BOARD_ID = "mb-000"

# Optional overrides:
# MQTT_HOST = "cmcm.local"
# NETWORK_DHCP = True
# STATIC_IP = "192.168.10.50"

# Ports listed here are treated as inputs and are not driven by the Morseboard.
RFID_INPUT_PORTS = {
    # 3: {
    #     "prop": "example_prop",
    #     "reader": 1,
    #     "correct_signal": "b",
    #     "wrong_signal": "a",
    # },
}

# Dry-contact switches default to Signal A with a pull-up and become active
# when the contact closes to GND.
SWITCH_INPUT_PORTS = {
    # 4: {
    #     "prop": "example_switch",
    #     "sensor": 1,
    #     "signal": "a",
    #     "active_value": 0,
    #     "pull": "up",
    #     "debounce_ms": 50,
    # },
}

# Two independent dry-contact inputs sharing one Morseboard port.
DUAL_SWITCH_INPUT_PORTS = {
    # 7: {
    #     "a": {"prop": "input_a", "active_value": 0, "pull": "up"},
    #     "b": {"prop": "input_b", "active_value": 0, "pull": "up"},
    # },
}

# Candle ports use Signal A as the candle LED output and Signal B as the
# active-low IR detection input.
# Set CANDLE_AUTO_TRIGGER_ENABLED = False to report IR changes without locally
# switching the candle output.
CANDLE_PORTS = {
    # 1: {
    #     "prop": "candle_1",
    #     "candle": 1,
    # },
}

# Demon knocker ports use Signal A as the solenoid output and Signal B as a
# directly driven NeoPixel data line. Keep commands/status as logical RGB; set
# pixel_color_order to "GRB" for LED batches with red/green swapped.
DEMON_KNOCKER_PORTS = {
    # 2: {
    #     "prop": "demon_knocker_1",
    #     "knocker": 1,
    #     "pixel_count": 1,
    #     "pixel_color_order": "RGB",
    #     "solenoid_active_low": False,
    # },
}

# Dual active-high latch-lock outputs. Commands use cmd/latch_lock/<label>.
# Requested durations are always clamped to max_pulse_ms.
LATCH_LOCK_PORTS = {
    # 5: {
    #     "prop": "example_latch_locks",
    #     "signal_a_lock": 2,
    #     "signal_b_lock": 13,
    #     "pulse_ms": 100,
    #     "max_pulse_ms": 100,
    # },
}

# Mixed output/input cross-drop port. Signal A is a bounded active-high
# solenoid pulse; Signal B is a debounced dry-contact input.
CROSS_DROP_PORTS = {
    # 8: {
    #     "prop": "cross_drop",
    #     "sensor": "cross",
    #     "active_value": 0,
    #     "pull": "up",
    #     "debounce_ms": 50,
    #     "pulse_ms": 500,
    #     "max_pulse_ms": 1000,
    # },
}

# Optional direct GPIO matrix for a ten-book bookshelf. Enabling this reserves
# every Morseboard port containing one of these GPIOs. Disable the DFPlayer if
# the matrix uses its UART pins GPIO0/GPIO1.
# DFPLAYER_ENABLED = False
# BOOKSHELF_MATRIX = {
#     "prop": "bookshelf",
#     "column_pins": (0, 1, 2, 3, 4),
#     "row_pins": (5, 6, 7, 8),  # shelf 1 out/in, then shelf 2 out/in
#     "discharge_ms": 10,
#     "settle_ms": 10,
#     "debounce_scans": 3,
# }

# Optional AS5600 safe-dial puzzle. The combination is checked locally and can
# be updated persistently through cmd/doorknob/config.
# DOORKNOB_PUZZLE = {
#     "i2c_id": 1,
#     "sda_pin": 10,
#     "scl_pin": 11,
#     "sequence": (
#         {"target": 0, "direction": "cw", "min_travel": 90},
#         {"target": 180, "direction": "ccw", "min_travel": 90},
#     ),
# }
