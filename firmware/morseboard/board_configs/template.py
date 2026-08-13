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
