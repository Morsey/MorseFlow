from machine import Pin, SPI
from time import sleep_ms, ticks_add, ticks_diff, ticks_ms
import network

try:
    import ujson as json
except ImportError:
    import json

import config
from mqtt_client import MQTTClient


def main():
    print("[net] starting W5500 network/MQTT test")
    nic = connect_network()
    print("[net] connected", nic.ifconfig())

    client = MQTTClient(
        config.MQTT_CLIENT_ID,
        config.MQTT_HOST,
        port=config.MQTT_PORT,
        user=config.MQTT_USERNAME,
        password=config.MQTT_PASSWORD,
        keepalive=config.MQTT_KEEPALIVE_SECONDS,
    )
    client.set_callback(on_message)
    client.connect(clean_session=True)
    print("[mqtt] connected to {}:{}".format(config.MQTT_HOST, config.MQTT_PORT))

    command_topic = topic("cmd/#")
    client.subscribe(command_topic, qos=config.MQTT_QOS)
    print("[mqtt] subscribed", command_topic)

    publish_json(client, "status", {
        "status": "online",
        "client_id": config.MQTT_CLIENT_ID,
        "ip": nic.ifconfig()[0],
        "test": "network_mqtt",
    }, retain=True)
    publish_json(client, "event", {
        "event": "started",
        "ip": nic.ifconfig()[0],
    })

    next_heartbeat_ms = ticks_ms()
    count = 0
    print("[test] send commands to", topic("cmd/test"))
    print("[test] press Ctrl-C to stop")
    try:
        while True:
            client.check_msg()
            now_ms = ticks_ms()
            if ticks_diff(now_ms, next_heartbeat_ms) >= 0:
                count += 1
                publish_json(client, "heartbeat", {
                    "status": "online",
                    "count": count,
                    "uptime_ms": now_ms,
                    "ip": nic.ifconfig()[0],
                })
                print("[mqtt] heartbeat", count)
                next_heartbeat_ms = ticks_add(now_ms, config.HEARTBEAT_INTERVAL_MS)
            sleep_ms(50)
    except KeyboardInterrupt:
        print("[test] stopping")
    finally:
        try:
            publish_json(client, "status", {
                "status": "stopped",
                "client_id": config.MQTT_CLIENT_ID,
            }, retain=True)
            client.disconnect()
        except Exception as exc:
            print("[mqtt] disconnect failed", repr(exc))


def connect_network():
    spi = SPI(
        config.ETH_SPI_BUS,
        baudrate=config.ETH_SPI_BAUDRATE,
        sck=Pin(config.ETH_SCK_PIN),
        mosi=Pin(config.ETH_MOSI_PIN),
        miso=Pin(config.ETH_MISO_PIN),
    )

    if hasattr(network, "WIZNET6K"):
        nic = network.WIZNET6K()
    else:
        nic = network.WIZNET5K(
            spi,
            Pin(config.ETH_CS_PIN),
            Pin(config.ETH_RST_PIN),
        )

    nic.active(True)
    if config.NETWORK_DHCP:
        try:
            nic.ifconfig("dhcp")
        except Exception as exc:
            print("[net] DHCP request method skipped", repr(exc))
    else:
        nic.ifconfig((
            config.STATIC_IP,
            config.STATIC_SUBNET,
            config.STATIC_GATEWAY,
            config.STATIC_DNS,
        ))

    start_ms = ticks_ms()
    while not nic.isconnected():
        if ticks_diff(ticks_ms(), start_ms) > config.NETWORK_TIMEOUT_MS:
            raise RuntimeError("network timeout; ifconfig={}".format(nic.ifconfig()))
        print("[net] waiting for link/DHCP", nic.ifconfig())
        sleep_ms(1000)
    return nic


def on_message(raw_topic, payload):
    message_topic = raw_topic.decode() if isinstance(raw_topic, bytes) else raw_topic
    message = payload.decode() if isinstance(payload, bytes) else payload
    print("[mqtt] received", message_topic, message)


def publish_json(client, suffix, payload, retain=False):
    client.publish(
        topic(suffix),
        json.dumps(payload),
        retain=retain,
        qos=config.MQTT_QOS,
    )


def topic(suffix):
    return "{}/{}".format(config.MQTT_TOPIC_ROOT, suffix)


if __name__ == "__main__":
    main()
