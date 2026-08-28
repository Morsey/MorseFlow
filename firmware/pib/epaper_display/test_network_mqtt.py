from time import sleep_ms, ticks_add, ticks_diff, ticks_ms

try:
    import ujson as json
except ImportError:
    import json

import config
from debug import log
from ethernet import EthernetService
from mqtt_client import MQTTClient


def main():
    log("test", "starting epaper network/MQTT test")
    ethernet = EthernetService()
    while not ethernet.is_ready():
        ethernet.update(ticks_ms())
        sleep_ms(100)

    ip_address = ethernet.ip_address()
    log("test", "network ready with IP {}".format(ip_address))

    client = MQTTClient(
        config.DEVICE_ID + "-test",
        config.MQTT_HOST,
        port=config.MQTT_PORT,
        user=config.MQTT_USERNAME,
        password=config.MQTT_PASSWORD,
        keepalive=config.MQTT_KEEPALIVE_SECONDS,
    )
    client.set_callback(_on_message)
    client.connect(clean_session=True)
    log("test", "MQTT connected to {}:{}".format(config.MQTT_HOST, config.MQTT_PORT))

    client.subscribe(_topic("cmd/#"), qos=0)
    log("test", "subscribed {}".format(_topic("cmd/#")))

    _publish_json(client, "status", {
        "status": "online",
        "device_id": config.DEVICE_ID,
        "firmware": config.FIRMWARE_NAME,
        "test": "network_mqtt",
        "ip": ip_address,
    }, retain=True)

    count = 0
    next_heartbeat_ms = ticks_ms()
    log("test", "send test messages to {}".format(_topic("cmd/test")))
    log("test", "press Ctrl-C to stop")
    try:
        while True:
            client.check_msg()
            now_ms = ticks_ms()
            if ticks_diff(now_ms, next_heartbeat_ms) >= 0:
                count += 1
                _publish_json(client, "heartbeat", {
                    "status": "online",
                    "device_id": config.DEVICE_ID,
                    "test": "network_mqtt",
                    "count": count,
                    "uptime_ms": now_ms,
                    "ip": ip_address,
                })
                log("test", "heartbeat {}".format(count))
                next_heartbeat_ms = ticks_add(now_ms, 10000)
            sleep_ms(50)
    except KeyboardInterrupt:
        log("test", "stopping")
    finally:
        try:
            _publish_json(client, "status", {
                "status": "stopped",
                "device_id": config.DEVICE_ID,
                "test": "network_mqtt",
            }, retain=True)
            client.disconnect()
        except Exception as exc:
            log("test", "disconnect failed {}".format(repr(exc)))


def _on_message(topic, payload):
    if isinstance(topic, bytes):
        topic = topic.decode("utf-8")
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    log("mqtt", "received {} {}".format(topic, payload))


def _publish_json(client, suffix, payload, retain=False):
    client.publish(
        _topic(suffix),
        json.dumps(payload),
        retain=retain,
        qos=0,
    )


def _topic(suffix):
    return "{}/{}".format(config.TOPIC_ROOT, suffix)


if __name__ == "__main__":
    main()
