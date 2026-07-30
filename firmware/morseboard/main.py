from machine import idle
from time import ticks_ms
import gc

from ethernet import EthernetService
from hardware import MorseboardHardware
from mqtt_service import MQTTService


def main():
    hardware = MorseboardHardware()
    ethernet = EthernetService()
    mqtt = MQTTService(hardware)

    hardware.safe_defaults()

    while True:
        now_ms = ticks_ms()
        ethernet.update(now_ms)
        mqtt.update(now_ms, ethernet.is_connected(), ethernet.ip_address())
        hardware.update(now_ms)

        if hardware.consume_dirty():
            mqtt.publish_state()

        gc.collect()
        idle()


main()

