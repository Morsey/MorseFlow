from machine import idle
from time import ticks_add, ticks_diff, ticks_ms
import gc

import config
from debug import log
from ethernet import EthernetService
from hardware import MorseboardHardware
from mqtt_service import MQTTService


def main():
    log("app", "starting MorseFlow Morseboard runtime")
    hardware = MorseboardHardware()
    ethernet = EthernetService()
    mqtt = MQTTService(hardware)

    hardware.safe_defaults()
    log("app", "safe defaults applied")

    # Cooperative service loop: each subsystem advances its own state machine.
    # Keep this loop free of blocking sleeps so MQTT and timed outputs stay live.
    next_error_log_ms = 0
    while True:
        now_ms = ticks_ms()
        try:
            ethernet.update(now_ms)
            mqtt.update(now_ms, ethernet.is_ready(), ethernet.ip_address())
            hardware.update(now_ms)

            if hardware.consume_dirty():
                mqtt.publish_state()
        except Exception as exc:
            if ticks_diff(now_ms, next_error_log_ms) >= 0:
                log("app", "loop error: {}".format(repr(exc)))
                next_error_log_ms = ticks_add(now_ms, config.APP_LOOP_ERROR_BACKOFF_MS)

        gc.collect()
        idle()


if __name__ == "__main__":
    main()
