import socket
import struct


class MQTTException(Exception):
    pass


class MQTTClient:
    def __init__(self, client_id, server, port=1883, user=None, password=None,
                 keepalive=0):
        self.client_id = _bytes(client_id)
        self.server = server
        self.port = port
        self.user = _bytes(user) if user is not None else None
        self.password = _bytes(password) if password is not None else None
        self.keepalive = keepalive
        self.sock = None
        self.callback = None
        self.pid = 0
        self.will = None

    def set_callback(self, callback):
        self.callback = callback

    def set_last_will(self, topic, message, retain=False, qos=0):
        self.will = (_bytes(topic), _bytes(message), retain, qos)

    def connect(self, clean_session=True):
        address = socket.getaddrinfo(self.server, self.port)[0][-1]
        self.sock = socket.socket()
        self.sock.connect(address)
        flags = 0x02 if clean_session else 0
        if self.will:
            flags |= 0x04 | (self.will[3] << 3)
            if self.will[2]:
                flags |= 0x20
        if self.user is not None:
            flags |= 0x80
            if self.password is not None:
                flags |= 0x40

        payload = bytearray()
        _append_string(payload, self.client_id)
        if self.will:
            _append_string(payload, self.will[0])
            _append_string(payload, self.will[1])
        if self.user is not None:
            _append_string(payload, self.user)
            if self.password is not None:
                _append_string(payload, self.password)

        variable = bytearray(b"\x00\x04MQTT\x04")
        variable.append(flags)
        variable.extend(struct.pack("!H", self.keepalive))
        packet = bytearray(b"\x10")
        _append_length(packet, len(variable) + len(payload))
        packet.extend(variable)
        packet.extend(payload)
        self.sock.write(packet)
        response = self.sock.read(4)
        if not response or len(response) != 4 or response[0] != 0x20 or response[3] != 0:
            raise MQTTException("invalid connack")

    def disconnect(self):
        if self.sock:
            try:
                self.sock.write(b"\xe0\x00")
            finally:
                self.sock.close()
                self.sock = None

    def publish(self, topic, message, retain=False, qos=0):
        topic = _bytes(topic)
        message = _bytes(message)
        variable = bytearray()
        _append_string(variable, topic)
        if qos:
            variable.extend(struct.pack("!H", self._next_pid()))
        packet = bytearray((0x30 | (qos << 1) | int(retain),))
        _append_length(packet, len(variable) + len(message))
        packet.extend(variable)
        packet.extend(message)
        self.sock.write(packet)
        if qos and self.wait_msg() != 0x40:
            raise MQTTException("expected puback")

    def subscribe(self, topic, qos=0):
        payload = bytearray()
        _append_string(payload, _bytes(topic))
        payload.append(qos)
        packet = bytearray(b"\x82")
        _append_length(packet, len(payload) + 2)
        packet.extend(struct.pack("!H", self._next_pid()))
        packet.extend(payload)
        self.sock.write(packet)
        if self.wait_msg() != 0x90:
            raise MQTTException("expected suback")

    def check_msg(self):
        self.sock.setblocking(False)
        try:
            return self.wait_msg()
        finally:
            self.sock.setblocking(True)

    def wait_msg(self):
        first = self.sock.read(1)
        if first is None:
            return None
        operation = first[0]
        remaining = self._read_length()
        packet_type = operation & 0xF0
        if packet_type == 0x30:
            topic_length = self._read_u16()
            topic = self.sock.read(topic_length)
            payload_length = remaining - topic_length - 2
            qos = (operation >> 1) & 0x03
            packet_id = None
            if qos:
                packet_id = self.sock.read(2)
                payload_length -= 2
            message = self.sock.read(payload_length) if payload_length else b""
            if self.callback:
                self.callback(topic, message)
            if qos == 1 and packet_id:
                self.sock.write(b"\x40\x02" + packet_id)
            return operation
        if remaining:
            self.sock.read(remaining)
        return packet_type

    def _next_pid(self):
        self.pid = self.pid % 65535 + 1
        return self.pid

    def _read_u16(self):
        data = self.sock.read(2)
        if not data or len(data) != 2:
            raise MQTTException("short read")
        return (data[0] << 8) | data[1]

    def _read_length(self):
        multiplier = 1
        value = 0
        while True:
            data = self.sock.read(1)
            if not data:
                raise MQTTException("short remaining length")
            value += (data[0] & 127) * multiplier
            if not data[0] & 128:
                return value
            multiplier *= 128


def _bytes(value):
    return value if isinstance(value, bytes) else str(value).encode("utf-8")


def _append_string(buffer, value):
    value = _bytes(value)
    buffer.extend(struct.pack("!H", len(value)))
    buffer.extend(value)


def _append_length(buffer, value):
    while True:
        encoded = value % 128
        value //= 128
        buffer.append(encoded | (0x80 if value else 0))
        if not value:
            return
