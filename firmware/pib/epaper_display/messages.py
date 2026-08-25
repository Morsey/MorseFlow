try:
    import ujson as json
except ImportError:
    import json

import config


def decode_payload(payload):
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    if not payload:
        return {}
    return json.loads(payload)


def encode_payload(payload):
    return json.dumps(payload)


def online_status(ip_address=None, uptime_ms=None, state=None):
    payload = {
        "status": "online",
        "device_id": config.DEVICE_ID,
        "firmware": config.FIRMWARE_NAME,
    }
    if ip_address:
        payload["ip"] = ip_address
    if uptime_ms is not None:
        payload["uptime_ms"] = uptime_ms
    if state is not None:
        payload["state"] = state
    return encode_payload(payload)


def offline_status():
    return encode_payload({
        "status": "offline",
        "device_id": config.DEVICE_ID,
    })


def state_payload(state):
    return encode_payload({
        "device_id": config.DEVICE_ID,
        "state": state,
    })


def event_payload(event_type, data):
    return encode_payload({
        "device_id": config.DEVICE_ID,
        "event": event_type,
        "data": data,
    })
