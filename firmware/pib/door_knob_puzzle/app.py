from machine import idle
from time import ticks_add, ticks_diff, ticks_ms
import gc

import config
from controller import DoorKnobController
from debug import log
from onboard_led import OnboardLED


def main():
    log("app", "starting DoorKnobPuzzle PIB")
    led = OnboardLED()
    controller = DoorKnobController()
    ethernet = None
    mqtt = None
    if config.MQTT_ENABLED:
        # Import networking only when enabled so local hardware tests also run
        # on standard MicroPython builds without the network module.
        from ethernet import EthernetService
        from mqtt_service import MQTTService
        ethernet = EthernetService()
        mqtt = MQTTService(controller)
    else:
        log("app", "networking and MQTT disabled")
    controller.safe_defaults()

    next_error_log_ms = 0
    next_network_wait_log_ms = 0
    next_local_test_log_ms = 0
    was_network_ready = False
    while True:
        now_ms = ticks_ms()
        try:
            led.update(now_ms, config.APP_LED_TOGGLE_MS)
            network_ready = False
            if ethernet is not None:
                ethernet.update(now_ms)
                network_ready = ethernet.is_ready()
                if network_ready and not was_network_ready:
                    log("app", "network connected with IP {}".format(ethernet.ip_address()))
                elif not network_ready and was_network_ready:
                    log("app", "network disconnected")
                if not network_ready and ticks_diff(now_ms, next_network_wait_log_ms) >= 0:
                    log("app", "network not ready")
                    next_network_wait_log_ms = ticks_add(
                        now_ms, config.NETWORK_WAIT_LOG_INTERVAL_MS
                    )
                was_network_ready = network_ready

            if mqtt is not None:
                mqtt.update(now_ms, network_ready, ethernet.ip_address())

            state_changed = controller.update(now_ms)
            for event_type, event_data in controller.consume_events():
                if mqtt is not None:
                    mqtt.publish_event(event_type, event_data)
                else:
                    log("event", "{} {}".format(event_type, event_data))
            if state_changed and mqtt is not None:
                mqtt.publish_state()

            if (
                mqtt is None
                and ticks_diff(now_ms, next_local_test_log_ms) >= 0
            ):
                log("test", controller.test_summary())
                next_local_test_log_ms = ticks_add(
                    now_ms, config.BOOK_TEST_LOG_INTERVAL_MS
                )
        except Exception as exc:
            if ticks_diff(now_ms, next_error_log_ms) >= 0:
                log("app", "loop error: {}".format(repr(exc)))
                next_error_log_ms = ticks_add(now_ms, config.APP_LOOP_ERROR_BACKOFF_MS)

        gc.collect()
        idle()


if __name__ == "__main__":
    main()
