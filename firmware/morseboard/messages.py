try:
    import ujson as json
except ImportError:
    import json


def decode_payload(payload):
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    if not payload:
        return {}
    return json.loads(payload)


def encode_payload(payload):
    return json.dumps(payload)


def online_status(board_id, ip_address=None, uptime_ms=None):
    payload = {
        "status": "online",
        "board_id": board_id,
        "firmware": "morseboard-skeleton",
    }
    if ip_address:
        payload["ip"] = ip_address
    if uptime_ms is not None:
        payload["uptime_ms"] = uptime_ms
    return encode_payload(payload)


def offline_status(board_id):
    return encode_payload({
        "status": "offline",
        "board_id": board_id,
    })


def state_payload(board_id, hardware_state):
    return encode_payload({
        "board_id": board_id,
        "state": hardware_state,
    })


def event_payload(board_id, event_type, data):
    return encode_payload({
        "board_id": board_id,
        "event": event_type,
        "data": data,
    })
