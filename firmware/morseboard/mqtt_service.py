from time import ticks_add, ticks_diff

from mqtt_client import MQTTClient

import config
from debug import log
import messages


class MQTTService:
    def __init__(self, hardware):
        self.hardware = hardware
        self.client = None
        self.connected = False
        self.start_ms = _ticks_ms()
        self.last_uptime_sample_ms = self.start_ms
        self.uptime_ms = 0
        self.next_attempt_ms = 0
        self.next_status_ms = 0
        self.last_error = None
        self.topic_root = config.TOPIC_ROOT

    def update(self, now_ms, network_connected, ip_address=None):
        self._update_uptime(now_ms)

        if not config.MQTT_ENABLED:
            if self.connected:
                self.connected = False
            return

        if not network_connected:
            if self.connected:
                log("mqtt", "network disconnected")
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
                self.publish_status(ip_address, now_ms)
                self.publish_state()
                self.next_status_ms = ticks_add(now_ms, config.STATUS_INTERVAL_MS)
        except Exception as exc:
            self.last_error = repr(exc)
            log("mqtt", "connection lost: {}".format(self.last_error))
            self.connected = False

    def publish_status(self, ip_address=None, now_ms=None):
        if not self.connected:
            return
        if now_ms is None:
            now_ms = _ticks_ms()
        try:
            self.client.publish(
                self._topic("status"),
                messages.online_status(
                    config.BOARD_ID,
                    ip_address,
                    self._uptime_ms(now_ms),
                ),
                retain=True,
                qos=config.MQTT_QOS,
            )
            log("mqtt", "published status")
        except Exception as exc:
            self._disconnect_after_error("publish status failed", exc)

    def publish_state(self):
        if not self.connected:
            return
        try:
            self.client.publish(
                self._topic("state"),
                messages.state_payload(config.BOARD_ID, self.hardware.state()),
                retain=True,
                qos=config.MQTT_QOS,
            )
            log("mqtt", "published state")
        except Exception as exc:
            self._disconnect_after_error("publish state failed", exc)

    def publish_event(self, event_type, data):
        if not self.connected:
            return
        try:
            self.client.publish(
                self._topic("event"),
                messages.event_payload(config.BOARD_ID, event_type, data),
                retain=False,
                qos=config.MQTT_QOS,
            )
            log("mqtt", "published event {}".format(event_type))
        except Exception as exc:
            self._disconnect_after_error("publish event failed", exc)

    def _connect(self, ip_address):
        try:
            log(
                "mqtt",
                "connecting client_id={} from ip={} to {}:{}".format(
                    config.BOARD_ID,
                    ip_address,
                    config.MQTT_HOST,
                    config.MQTT_PORT,
                ),
            )
            client_id = config.BOARD_ID
            self.client = MQTTClient(
                client_id,
                config.MQTT_HOST,
                port=config.MQTT_PORT,
                user=config.MQTT_USERNAME,
                password=config.MQTT_PASSWORD,
                keepalive=config.MQTT_KEEPALIVE_SECONDS,
            )
            self.client.set_last_will(
                self._topic("status"),
                messages.offline_status(config.BOARD_ID),
                retain=True,
                qos=config.MQTT_QOS,
            )
            self.client.set_callback(self._on_message)
            self.client.connect(clean_session=True)
            self._subscribe_commands()
            self.connected = True
            self.last_error = None
            self.publish_status(ip_address, _ticks_ms())
            self.publish_state()
            if self.connected:
                log("mqtt", "connected and subscribed")
        except Exception as exc:
            self.last_error = repr(exc)
            self.connected = False
            log("mqtt", "connect failed: {}".format(self.last_error))
            try:
                if self.client:
                    self.client.disconnect()
            except Exception:
                pass

    def _subscribe_commands(self):
        self.client.subscribe(self._topic("cmd/#"), qos=config.MQTT_QOS)
        log("mqtt", "subscribed {}".format(self._topic("cmd/#")))

    def _on_message(self, topic, payload):
        now_ms = _ticks_ms()
        topic = _to_text(topic)
        command = messages.decode_payload(payload)
        suffix = topic[len(self.topic_root) + 1:]
        log("mqtt", "received {} {}".format(suffix, command))

        if suffix == "cmd/power":
            self.hardware.set_power(bool(command.get("enabled")))
        elif suffix == "cmd/relay":
            self.hardware.set_relay(bool(command.get("enabled")))
        elif suffix == "cmd/audio":
            self.hardware.command_audio(command)
        elif suffix == "cmd/sequence":
            self.hardware.command_sequence(command, now_ms)
        elif suffix == "cmd/status":
            self.publish_status(now_ms=now_ms)
            self.publish_state()
        elif suffix.startswith("cmd/port/"):
            port_number = int(suffix.split("/")[-1])
            self.hardware.command_port(port_number, command, now_ms)

    def _topic(self, suffix):
        return "{}/{}".format(self.topic_root, suffix)

    def _uptime_ms(self, now_ms):
        self._update_uptime(now_ms)
        return self.uptime_ms

    def _update_uptime(self, now_ms):
        elapsed_ms = ticks_diff(now_ms, self.last_uptime_sample_ms)
        if elapsed_ms > 0:
            self.uptime_ms += elapsed_ms
            self.last_uptime_sample_ms = now_ms

    def _disconnect_after_error(self, context, exc):
        self.last_error = repr(exc)
        log("mqtt", "{}: {}".format(context, self.last_error))
        self.connected = False
        try:
            if self.client:
                self.client.disconnect()
        except Exception:
            pass


def _to_text(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def _ticks_ms():
    from time import ticks_ms
    return ticks_ms()
