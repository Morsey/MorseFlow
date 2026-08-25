from machine import idle
from time import ticks_add, ticks_diff, ticks_ms
import gc

import config
from debug import log
from display_controller import DisplayController
from ethernet import EthernetService
from http_service import HTTPService
from mqtt_service import MQTTService


def main():
    log("app", "starting epaper display PIB")
    display = DisplayController()
    ethernet = EthernetService()
    mqtt = MQTTService(display)
    http = HTTPService(display)

    display.init()
    next_error_log_ms = 0
    next_network_wait_log_ms = 0
    was_network_ready = False

    def publish_display_event(event_type, event_data):
        mqtt.publish_event(event_type, event_data)
        mqtt.publish_status(ethernet.ip_address(), ticks_ms())
        mqtt.publish_state()

    while True:
        now_ms = ticks_ms()
        try:
            ethernet.update(now_ms)
            network_ready = ethernet.is_ready()
            if network_ready:
                if not was_network_ready:
                    log("app", "network connected with IP {}".format(ethernet.ip_address()))
                was_network_ready = True
            else:
                if was_network_ready:
                    log("app", "network disconnected")
                    http.stop()
                was_network_ready = False
                if ticks_diff(now_ms, next_network_wait_log_ms) >= 0:
                    log("app", "network not ready")
                    next_network_wait_log_ms = ticks_add(
                        now_ms,
                        config.NETWORK_WAIT_LOG_INTERVAL_MS,
                    )

            http.update(network_ready)
            mqtt.update(now_ms, network_ready, ethernet.ip_address())

            if display.update(publish_display_event):
                mqtt.publish_state()

            for event_type, event_data in display.consume_events():
                mqtt.publish_event(event_type, event_data)
                mqtt.publish_status(ethernet.ip_address(), now_ms)
        except Exception as exc:
            if ticks_diff(now_ms, next_error_log_ms) >= 0:
                log("app", "loop error: {}".format(repr(exc)))
                next_error_log_ms = ticks_add(now_ms, config.APP_LOOP_ERROR_BACKOFF_MS)

        gc.collect()
        idle()


if __name__ == "__main__":
    main()
