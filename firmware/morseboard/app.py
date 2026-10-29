from machine import idle
from time import ticks_add, ticks_diff, ticks_ms
import gc

import config
from debug import log
from ethernet import EthernetService
from hardware import MorseboardHardware
from mqtt_service import MQTTService
from onboard_led import OnboardLED


def main():
    log("app", "starting MorseFlow Morseboard runtime")
    status_led = OnboardLED()
    log("app", "creating hardware")
    hardware = MorseboardHardware()
    ethernet = None
    mqtt = None
    if config.MQTT_ENABLED:
        log("app", "creating ethernet service")
        ethernet = EthernetService()
        log("app", "creating MQTT service")
        mqtt = MQTTService(hardware)
    else:
        log("app", "MQTT disabled; Ethernet service not started")

    hardware.safe_defaults()
    log("app", "safe defaults applied")

    # Cooperative service loop: each subsystem advances its own state machine.
    # Keep this loop free of blocking sleeps so MQTT and timed outputs stay live.
    next_error_log_ms = 0
    next_network_wait_log_ms = 0
    next_doorknob_repl_ms = 0
    was_network_ready = False
    while True:
        now_ms = ticks_ms()
        try:
            status_led.update(now_ms, config.APP_LED_TOGGLE_MS)
            network_ready = False
            if ethernet is not None:
                ethernet.update(now_ms)
                network_ready = ethernet.is_ready()

            if network_ready:
                if not was_network_ready:
                    log("app", "network connected with IP {}".format(ethernet.ip_address()))
                was_network_ready = True
                mqtt.update(now_ms, True, ethernet.ip_address())
            elif ethernet is not None:
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

            if (
                getattr(config, "REPL_EVENT_LOGGING", False)
                and hardware.doorknob is not None
                and ticks_diff(now_ms, next_doorknob_repl_ms) >= 0
            ):
                log("knob", hardware.doorknob.repl_status())
                next_doorknob_repl_ms = ticks_add(
                    now_ms,
                    getattr(config, "DOORKNOB_REPL_INTERVAL_MS", 250),
                )

            for event_type, event_data in hardware.consume_events():
                if getattr(config, "REPL_EVENT_LOGGING", False):
                    if event_type == "doorknob":
                        log(
                            "knob",
                            "event={} step={}/{}".format(
                                event_data.get("reason"),
                                event_data.get("step_index"),
                                event_data.get("step_count"),
                            ),
                        )
                    else:
                        log("event", "{} {}".format(event_type, event_data))
                if mqtt is not None:
                    mqtt.publish_event(event_type, event_data)

            if hardware.consume_dirty():
                if mqtt is not None:
                    mqtt.publish_state()
        except Exception as exc:
            if ticks_diff(now_ms, next_error_log_ms) >= 0:
                log("app", "loop error: {}".format(repr(exc)))
                next_error_log_ms = ticks_add(now_ms, config.APP_LOOP_ERROR_BACKOFF_MS)

        gc.collect()
        idle()


if __name__ == "__main__":
    main()
