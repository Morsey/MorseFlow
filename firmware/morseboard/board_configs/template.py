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

# Candle ports use Signal A as the candle LED output and Signal B as the
# active-low IR detection input.
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
