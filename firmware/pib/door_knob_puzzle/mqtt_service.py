from time import ticks_add, ticks_diff, ticks_ms

import config
from debug import log
import messages
from mqtt_client import MQTTClient


class MQTTService:
    def __init__(self, controller):
        self.controller = controller
        self.client = None
        self.connected = False
        self.last_sample_ms = ticks_ms()
        self.uptime_ms = 0
        self.next_attempt_ms = 0
        self.next_status_ms = 0
        self.last_error = None

    def update(self, now_ms, network_ready, ip_address=None):
        elapsed = ticks_diff(now_ms, self.last_sample_ms)
        if elapsed > 0:
            self.uptime_ms += elapsed
            self.last_sample_ms = now_ms
        if not network_ready:
            self.connected = False
            return
        if not self.connected:
            if ticks_diff(now_ms, self.next_attempt_ms) >= 0:
                self.next_attempt_ms = ticks_add(now_ms, config.RECONNECT_INTERVAL_MS)
                self._connect(ip_address)
            return
        try:
            self.client.check_msg()
            if ticks_diff(now_ms, self.next_status_ms) >= 0:
                self.publish_status(ip_address)
                self.publish_state()
                self.next_status_ms = ticks_add(now_ms, config.STATUS_INTERVAL_MS)
        except Exception as exc:
            self._fail("connection lost", exc)

    def publish_status(self, ip_address=None):
        self._publish("status", messages.online_status(
            ip_address, self.uptime_ms, self.controller.state()
        ), True)

    def publish_state(self):
        self._publish("state", messages.state_payload(self.controller.state()), True)

    def publish_event(self, event_type, data):
        self._publish("event", messages.event_payload(event_type, data), False)

    def _publish(self, suffix, payload, retain):
        if not self.connected:
            return
        try:
            self.client.publish(self._topic(suffix), payload, retain=retain,
                                qos=config.MQTT_QOS)
        except Exception as exc:
            self._fail("publish {} failed".format(suffix), exc)

    def _connect(self, ip_address):
        try:
            self.client = MQTTClient(
                config.DEVICE_ID, config.MQTT_HOST, port=config.MQTT_PORT,
                user=config.MQTT_USERNAME, password=config.MQTT_PASSWORD,
                keepalive=config.MQTT_KEEPALIVE_SECONDS,
            )
            self.client.set_last_will(
                self._topic("status"), messages.offline_status(),
                retain=True, qos=config.MQTT_QOS,
            )
            self.client.set_callback(self._on_message)
            self.client.connect(clean_session=True)
            self.client.subscribe(self._topic("cmd/#"), qos=config.MQTT_QOS)
            self.connected = True
            self.last_error = None
            self.publish_status(ip_address)
            self.publish_state()
            log("mqtt", "connected and subscribed")
        except Exception as exc:
            self._fail("connect failed", exc)

    def _on_message(self, topic, payload):
        topic = topic.decode("utf-8") if isinstance(topic, bytes) else topic
        command = messages.decode_payload(payload)
        suffix = topic[len(config.TOPIC_ROOT) + 1:]
        name = suffix[4:] if suffix.startswith("cmd/") else ""
        if name == "status":
            self.publish_status()
            self.publish_state()
        elif self.controller.command(name, command, ticks_ms()):
            self.publish_state()
        else:
            log("mqtt", "ignored command topic {}".format(suffix))

    def _topic(self, suffix):
        return "{}/{}".format(config.TOPIC_ROOT, suffix)

    def _fail(self, context, exc):
        self.last_error = repr(exc)
        self.connected = False
        log("mqtt", "{}: {}".format(context, self.last_error))
        try:
            if self.client:
                self.client.disconnect()
        except Exception:
            pass
