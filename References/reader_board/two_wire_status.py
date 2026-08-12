"""
Small software two-wire status slave for RP2040 reader boards.

The controller is always the master. Both lines idle high through pull-ups and
devices only ever drive them low. The master holds a start condition (DATA low
while CLK is high), sends one command byte, then releases DATA and clocks out a
fixed-length response from the reader.

Status response frame, 24 bytes:
  0..1  magic "MR"
  2     protocol version
  3     flags: bit0 card present, bit2 reader ok, bit3 scan error
  4     status sequence, increments on state changes
  5..6  age of the current state in milliseconds, little endian, saturated
  7     UID length in bytes
  8..17 UID bytes, zero-padded
  18    present card count
  19    card type: 1 ISO14443, 2 ISO15693
  20    error code: 0 none, 1 scan/init error, 2 unknown command
  21    reserved
  22    CRC-8/ATM over bytes 0..21
  23    newline sentinel
"""

from machine import Pin
from utime import sleep_us, ticks_diff, ticks_us


CMD_PING = 0x00
CMD_STATUS = 0x01

STATUS_FRAME_LENGTH = 24
MAGIC_0 = 0x4D  # M
MAGIC_1 = 0x52  # R
PROTOCOL_VERSION = 1


def crc8(data, length):
    """CRC-8/ATM over the first length bytes."""
    crc = 0
    for i in range(length):
        crc ^= data[i]
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


class TwoWireStatusSlave:
    """Polled I2C-like slave using arbitrary GPIO pins.

    The class deliberately avoids hardware I2C/UART/SPI peripherals so CLK and
    DATA can be any GPIOs. Call service() often from the main loop. If the reader
    is busy scanning a card, the controller should retry the transaction.
    """

    def __init__(self, clk_pin, data_pin, frame_provider, bit_timeout_us=3000):
        self.clk = Pin(clk_pin, Pin.IN, Pin.PULL_UP)
        self.data = Pin(data_pin, Pin.IN, Pin.PULL_UP)
        self.frame_provider = frame_provider
        self.bit_timeout_us = bit_timeout_us
        self.transaction_count = 0
        self.timeout_count = 0
        self.last_command = None
        self.release_data()

    def release_data(self):
        self.data.init(Pin.IN, Pin.PULL_UP)

    def drive_data_low(self):
        self.data.init(Pin.OUT)
        self.data.value(0)

    def _wait_pin(self, pin, level, timeout_us=None):
        if timeout_us is None:
            timeout_us = self.bit_timeout_us
        start = ticks_us()
        while pin.value() != level:
            if ticks_diff(ticks_us(), start) > timeout_us:
                return False
            sleep_us(5)
        return True

    def _wait_clock_high(self):
        return self._wait_pin(self.clk, 1)

    def _wait_clock_low(self):
        return self._wait_pin(self.clk, 0)

    def _start_pending(self):
        return self.clk.value() == 1 and self.data.value() == 0

    def _read_command_byte(self):
        value = 0
        self.release_data()
        for _ in range(8):
            if not self._wait_clock_high():
                return None
            value = (value << 1) | (1 if self.data.value() else 0)
            if not self._wait_clock_low():
                return None
        return value

    def _ack_command(self):
        self.drive_data_low()
        if not self._wait_clock_high():
            self.release_data()
            return False
        if not self._wait_clock_low():
            self.release_data()
            return False
        self.release_data()
        return True

    def _write_byte(self, value):
        for bit in range(7, -1, -1):
            if value & (1 << bit):
                self.release_data()
            else:
                self.drive_data_low()
            if not self._wait_clock_high():
                self.release_data()
                return False
            if not self._wait_clock_low():
                self.release_data()
                return False
        self.release_data()
        return True

    def _response_for_command(self, command):
        frame = self.frame_provider()
        if command == CMD_PING:
            frame[3] |= 0x80
        elif command != CMD_STATUS:
            frame[20] = 2
            frame[22] = crc8(frame, 22)
        return frame

    def service(self, max_wait_us=0):
        """Serve one transaction if the controller has started one.

        Returns True when a transaction was completed. max_wait_us can be used
        to wait briefly for a start condition; the default is a non-blocking poll.
        """
        self.release_data()

        if max_wait_us:
            start = ticks_us()
            while not self._start_pending():
                if ticks_diff(ticks_us(), start) > max_wait_us:
                    return False
                sleep_us(10)
        elif not self._start_pending():
            return False

        # Consume the start condition. The first command bit is sampled on the
        # next rising edge after the master has pulled CLK low.
        if not self._wait_clock_low():
            self.timeout_count += 1
            self.release_data()
            return False

        command = self._read_command_byte()
        if command is None:
            self.timeout_count += 1
            self.release_data()
            return False

        self.last_command = command
        frame = self._response_for_command(command)

        if not self._ack_command():
            self.timeout_count += 1
            return False

        for value in frame:
            if not self._write_byte(value):
                self.timeout_count += 1
                return False

        self.transaction_count += 1
        self.release_data()
        return True


def build_status_frame(flags, sequence, age_ms, uid_hex, card_count,
                       card_type_code, error_code):
    """Build the fixed-length response frame served by TwoWireStatusSlave."""
    frame = bytearray(STATUS_FRAME_LENGTH)
    frame[0] = MAGIC_0
    frame[1] = MAGIC_1
    frame[2] = PROTOCOL_VERSION
    frame[3] = flags & 0xFF
    frame[4] = sequence & 0xFF

    if age_ms < 0:
        age_ms = 0
    if age_ms > 65535:
        age_ms = 65535
    frame[5] = age_ms & 0xFF
    frame[6] = (age_ms >> 8) & 0xFF

    uid_len = 0
    if uid_hex:
        max_hex_chars = 20
        clipped = uid_hex[:max_hex_chars]
        uid_len = len(clipped) // 2
        for i in range(uid_len):
            frame[8 + i] = int(clipped[i * 2:i * 2 + 2], 16)
    frame[7] = uid_len

    if card_count > 255:
        card_count = 255
    frame[18] = card_count & 0xFF
    frame[19] = card_type_code & 0xFF
    frame[20] = error_code & 0xFF
    frame[21] = 0
    frame[22] = crc8(frame, 22)
    frame[23] = 0x0A
    return frame
