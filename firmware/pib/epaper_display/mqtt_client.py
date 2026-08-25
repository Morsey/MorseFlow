import socket
import struct


class MQTTException(Exception):
    pass


class MQTTClient:
    def __init__(
        self,
        client_id,
        server,
        port=0,
        user=None,
        password=None,
        keepalive=0,
        ssl=False,
        ssl_params=None,
    ):
        if port == 0:
            port = 8883 if ssl else 1883
        self.client_id = _bytes(client_id)
        self.server = server
        self.port = port
        self.user = _bytes(user) if user is not None else None
        self.password = _bytes(password) if password is not None else None
        self.keepalive = keepalive
        self.ssl = ssl
        self.ssl_params = ssl_params or {}
        self.sock = None
        self.cb = None
        self.pid = 0
        self.lw_topic = None
        self.lw_msg = None
        self.lw_qos = 0
        self.lw_retain = False

    def set_callback(self, f):
        self.cb = f

    def set_last_will(self, topic, msg, retain=False, qos=0):
        if qos not in (0, 1):
            raise MQTTException("unsupported will QoS")
        self.lw_topic = _bytes(topic)
        self.lw_msg = _bytes(msg)
        self.lw_qos = qos
        self.lw_retain = retain

    def connect(self, clean_session=True):
        addr = socket.getaddrinfo(self.server, self.port)[0][-1]
        self.sock = socket.socket()
        self.sock.connect(addr)
        if self.ssl:
            import ssl
            self.sock = ssl.wrap_socket(self.sock, **self.ssl_params)

        flags = 0
        if clean_session:
            flags |= 0x02
        if self.lw_topic:
            flags |= 0x04 | (self.lw_qos << 3)
            if self.lw_retain:
                flags |= 0x20
        if self.user is not None:
            flags |= 0x80
            if self.password is not None:
                flags |= 0x40

        payload = bytearray()
        _append_str(payload, self.client_id)
        if self.lw_topic:
            _append_str(payload, self.lw_topic)
            _append_str(payload, self.lw_msg)
        if self.user is not None:
            _append_str(payload, self.user)
            if self.password is not None:
                _append_str(payload, self.password)

        variable_header = bytearray(b"\x00\x04MQTT\x04")
        variable_header.append(flags)
        variable_header.extend(struct.pack("!H", self.keepalive))

        packet = bytearray(b"\x10")
        _append_remaining_length(packet, len(variable_header) + len(payload))
        packet.extend(variable_header)
        packet.extend(payload)
        self.sock.write(packet)

        response = self.sock.read(4)
        if response is None or len(response) != 4 or response[0] != 0x20 or response[1] != 0x02:
            raise MQTTException("invalid connack")
        if response[3] != 0:
            raise MQTTException(response[3])
        return response[2] & 1

    def disconnect(self):
        if self.sock:
            try:
                self.sock.write(b"\xe0\x00")
            finally:
                self.sock.close()
                self.sock = None

    def ping(self):
        self.sock.write(b"\xc0\x00")

    def publish(self, topic, msg, retain=False, qos=0):
        if qos not in (0, 1):
            raise MQTTException("unsupported publish QoS")
        topic = _bytes(topic)
        msg = _bytes(msg)
        header = 0x30 | (qos << 1) | (1 if retain else 0)

        variable_header = bytearray()
        _append_str(variable_header, topic)
        if qos:
            pid = self._next_pid()
            variable_header.extend(struct.pack("!H", pid))

        packet = bytearray()
        packet.append(header)
        _append_remaining_length(packet, len(variable_header) + len(msg))
        packet.extend(variable_header)
        packet.extend(msg)
        self.sock.write(packet)

        if qos:
            op = self.wait_msg()
            if op != 0x40:
                raise MQTTException("expected puback")

    def subscribe(self, topic, qos=0):
        if qos not in (0, 1):
            raise MQTTException("unsupported subscribe QoS")
        topic = _bytes(topic)
        pid = self._next_pid()

        payload = bytearray()
        _append_str(payload, topic)
        payload.append(qos)

        packet = bytearray(b"\x82")
        _append_remaining_length(packet, 2 + len(payload))
        packet.extend(struct.pack("!H", pid))
        packet.extend(payload)
        self.sock.write(packet)

        op = self.wait_msg()
        if op != 0x90:
            raise MQTTException("expected suback")

    def check_msg(self):
        self.sock.setblocking(False)
        try:
            return self.wait_msg()
        finally:
            self.sock.setblocking(True)

    def wait_msg(self):
        response = self.sock.read(1)
        if response is None:
            return None
        op = response[0]

        remaining_length = self._read_remaining_length()
        if op == 0xD0:
            if remaining_length:
                self.sock.read(remaining_length)
            return op

        packet_type = op & 0xF0
        if packet_type == 0x30:
            topic_len = self._read_u16()
            topic = self.sock.read(topic_len)
            payload_len = remaining_length - topic_len - 2
            qos = (op >> 1) & 0x03
            pid = None
            if qos:
                pid = self.sock.read(2)
                payload_len -= 2
            msg = self.sock.read(payload_len) if payload_len else b""
            if self.cb:
                self.cb(topic, msg)
            if qos == 1 and pid:
                self.sock.write(b"\x40\x02" + pid)
            return op

        if packet_type in (0x40, 0x90):
            if remaining_length:
                self.sock.read(remaining_length)
            return packet_type

        if remaining_length:
            self.sock.read(remaining_length)
        return packet_type

    def _next_pid(self):
        self.pid += 1
        if self.pid > 65535:
            self.pid = 1
        return self.pid

    def _read_u16(self):
        data = self.sock.read(2)
        if data is None or len(data) != 2:
            raise MQTTException("short read")
        return (data[0] << 8) | data[1]

    def _read_remaining_length(self):
        multiplier = 1
        value = 0
        while True:
            encoded = self.sock.read(1)
            if encoded is None or len(encoded) != 1:
                raise MQTTException("short remaining length")
            encoded = encoded[0]
            value += (encoded & 127) * multiplier
            if (encoded & 128) == 0:
                return value
            multiplier *= 128
            if multiplier > 128 * 128 * 128:
                raise MQTTException("bad remaining length")


def _bytes(value):
    if isinstance(value, bytes):
        return value
    return str(value).encode("utf-8")


def _append_str(buf, value):
    value = _bytes(value)
    buf.extend(struct.pack("!H", len(value)))
    buf.extend(value)


def _append_remaining_length(buf, value):
    while True:
        encoded = value % 128
        value //= 128
        if value > 0:
            encoded |= 128
        buf.append(encoded)
        if value == 0:
            break

