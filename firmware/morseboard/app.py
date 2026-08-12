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
    log("app", "creating hardware")
    hardware = MorseboardHardware()
    log("app", "creating ethernet service")
    ethernet = EthernetService()
    log("app", "creating MQTT service")
    mqtt = MQTTService(hardware)

    hardware.safe_defaults()
    log("app", "safe defaults applied")

    # Cooperative service loop: each subsystem advances its own state machine.
    # Keep this loop free of blocking sleeps so MQTT and timed outputs stay live.
    next_error_log_ms = 0
    next_network_wait_log_ms = 0
    was_network_ready = False
    while True:
        now_ms = ticks_ms()
        try:
            ethernet.update(now_ms)
            network_ready = ethernet.is_ready()

            if network_ready:
                if not was_network_ready:
                    log("app", "network connected with IP {}".format(ethernet.ip_address()))
                was_network_ready = True
                mqtt.update(now_ms, True, ethernet.ip_address())
            else:
                if was_network_ready:
                    log("app", "network disconnected; MQTT stopped")
                was_network_ready = False
                if ticks_diff(now_ms, next_network_wait_log_ms) >= 0:
                    log("app", "network not ready; MQTT not started")
                    next_network_wait_log_ms = ticks_add(
                        now_ms,
                        config.NETWORK_WAIT_LOG_INTERVAL_MS,
                    )

            hardware.update(now_ms)

            for event_type, event_data in hardware.consume_events():
                mqtt.publish_event(event_type, event_data)

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
