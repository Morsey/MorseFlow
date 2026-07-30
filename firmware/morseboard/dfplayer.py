from machine import Pin, UART

import pins


class DFPlayer:
    CMD_PLAY_TRACK = 0x03
    CMD_SET_VOLUME = 0x06
    CMD_STOP = 0x16

    def __init__(self, uart_id=0, baudrate=9600):
        self.uart = UART(
            uart_id,
            baudrate=baudrate,
            tx=Pin(pins.DFPLAYER_TX),
            rx=Pin(pins.DFPLAYER_RX),
        )

    def send(self, command, parameter=0):
        frame = [
            0x7E,
            0xFF,
            0x06,
            command,
            0x00,
            (parameter >> 8) & 0xFF,
            parameter & 0xFF,
            0x00,
            0x00,
            0xEF,
        ]
        checksum = 0 - sum(frame[1:7])
        frame[7] = (checksum >> 8) & 0xFF
        frame[8] = checksum & 0xFF
        self.uart.write(bytes(frame))

    def play_track(self, track_number):
        self.send(self.CMD_PLAY_TRACK, int(track_number))

    def set_volume(self, volume):
        volume = max(0, min(30, int(volume)))
        self.send(self.CMD_SET_VOLUME, volume)

    def stop(self):
        self.send(self.CMD_STOP, 0)

