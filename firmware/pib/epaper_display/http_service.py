try:
    import usocket as socket
except ImportError:
    import socket

try:
    import ujson as json
except ImportError:
    import json

import config
from debug import log
from display_controller import (
    fs_free_bytes,
    list_images,
    safe_image_name,
    upload_path,
    url_decode,
    validate_image_size,
)
from epaper_display import BUFFER_SIZE


class HTTPService:
    def __init__(self, display):
        self.display = display
        self.server = None
        self.last_error = None

    def update(self, network_ready):
        if not config.HTTP_ENABLED:
            self.stop()
            return
        if not network_ready:
            self.stop()
            return
        if self.server is None:
            self.start()
        self._accept_one()

    def start(self):
        self.stop()
        self.server = socket.socket()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("0.0.0.0", config.HTTP_PORT))
        self.server.listen(1)
        self.server.settimeout(0)
        log("http", "listening on port {}".format(config.HTTP_PORT))

    def stop(self):
        if self.server is not None:
            try:
                self.server.close()
            except Exception:
                pass
        self.server = None

    def _accept_one(self):
        try:
            client, addr = self.server.accept()
        except OSError:
            return
        log("http", "connection {}".format(addr))
        client.settimeout(5)
        try:
            self._handle_client(client)
        except Exception as exc:
            self.last_error = repr(exc)
            log("http", "error {}".format(self.last_error))
            try:
                _json(client, b"500 Internal Server Error", {"error": self.last_error})
            except Exception:
                pass
        finally:
            try:
                client.close()
            except Exception:
                pass

    def _handle_client(self, client):
        line = _readline(client)
        if not line:
            return
        parts = line.decode().strip().split()
        if len(parts) < 2:
            _send(client, b"400 Bad Request", body="bad request")
            return
        method, raw_path = parts[0], parts[1]
        headers = {}
        while True:
            line = _readline(client)
            if not line or line == b"\r\n":
                break
            key, value = line.decode().split(":", 1)
            headers[key.lower()] = value.strip()

        path, query = _parse_query(raw_path)
        content_length = int(headers.get("content-length", "0"))

        if method == "GET" and path == "/":
            self._index(client)
        elif method == "GET" and path == "/status":
            _json(client, b"200 OK", self.display.state())
        elif method == "GET" and path == "/images":
            _json(client, b"200 OK", {"images": list_images(), "free_bytes": fs_free_bytes()})
        elif method == "PUT" and path.startswith("/images/"):
            name = safe_image_name(path[len("/images/"):])
            self._upload(client, name, content_length)
            _json(client, b"200 OK", {"status": "uploaded", "image": name})
        elif method == "DELETE" and path.startswith("/images/"):
            name = safe_image_name(path[len("/images/"):])
            self.display.delete_image(name)
            _json(client, b"200 OK", {"status": "deleted", "image": name})
        elif method == "POST" and path == "/show":
            if "image" in query:
                image = safe_image_name(query["image"])
                self.display.queue_show(image)
                _json(client, b"202 Accepted", {"status": "queued", "image": image})
            elif query.get("color") in ("white", "black"):
                color = query["color"]
                self.display.queue_clear(color)
                _json(client, b"202 Accepted", {"status": "queued", "color": color})
            else:
                _send(client, b"400 Bad Request", body="missing image or color")
        else:
            _send(client, b"404 Not Found", body="not found")

    def _upload(self, client, name, content_length):
        if content_length != BUFFER_SIZE:
            raise ValueError("upload must be {} bytes".format(BUFFER_SIZE))
        if fs_free_bytes() < content_length + config.RESERVED_FREE_BYTES:
            raise OSError("not enough free space")

        path = upload_path(name)
        tmp_path = path + ".tmp"
        remaining = content_length
        try:
            with open(tmp_path, "wb") as file:
                while remaining:
                    chunk = client.recv(min(1024, remaining))
                    if not chunk:
                        raise OSError("upload interrupted")
                    file.write(chunk)
                    remaining -= len(chunk)
            validate_image_size(tmp_path)
            try:
                import os
                os.remove(path)
            except OSError:
                pass
            import os
            os.rename(tmp_path, path)
        except Exception:
            try:
                import os
                os.remove(tmp_path)
            except OSError:
                pass
            raise

    def _index(self, client):
        items = ""
        options = ""
        for item in list_images():
            name = item["name"]
            escaped_name = _escape(name)
            items += (
                "<li><b>{}</b> {} bytes "
                "<button onclick=\"showImage('{}')\">Show</button> "
                "<button onclick=\"deleteImage('{}')\">Delete</button></li>"
            ).format(escaped_name, item["size"], escaped_name, escaped_name)
            options += "<option value=\"{}\">{} ({} bytes)</option>".format(
                escaped_name,
                escaped_name,
                item["size"],
            )
        if not options:
            options = "<option value=\"\">No .bin files found</option>"
        body = """<!doctype html>
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Epaper PIB</title></head><body>
<h1>Epaper PIB</h1>
<p>Current: {current}<br>Busy: {busy}<br>Free: {free} bytes</p>
<label for="image">Image</label>
<select id="image">{options}</select>
<button onclick="showSelected()">Show selected</button>
<button onclick="location.reload()">Refresh list</button>
<hr>
<input id="file" type="file" accept=".bin">
<button onclick="upload()">Upload .bin</button>
<button onclick="showColor('white')">White</button>
<button onclick="showColor('black')">Black</button>
<ul>{items}</ul>
<pre id="out"></pre>
<script>
function log(t){{document.getElementById('out').textContent=t}}
function upload(){{
 const f=document.getElementById('file').files[0]; if(!f){{log('choose a file');return}}
 fetch('/images/'+encodeURIComponent(f.name),{{method:'PUT',body:f}}).then(r=>r.text()).then(t=>{{log(t);setTimeout(()=>location.reload(),500)}})
}}
function showSelected(){{
 const n=document.getElementById('image').value; if(!n){{log('no image selected');return}}
 showImage(n)
}}
function showImage(n){{fetch('/show?image='+encodeURIComponent(n),{{method:'POST'}}).then(r=>r.text()).then(log)}}
function showColor(c){{fetch('/show?color='+c,{{method:'POST'}}).then(r=>r.text()).then(log)}}
function deleteImage(n){{fetch('/images/'+encodeURIComponent(n),{{method:'DELETE'}}).then(r=>r.text()).then(t=>{{log(t);setTimeout(()=>location.reload(),500)}})}}
</script></body></html>""".format(
            current=self.display.current_image or self.display.current_color,
            busy=self.display.busy,
            free=fs_free_bytes(),
            options=options,
            items=items,
        )
        _send(client, b"200 OK", b"text/html", body)


def _readline(sock):
    line = bytearray()
    while True:
        char = sock.recv(1)
        if not char:
            break
        line.append(char[0])
        if char == b"\n":
            break
    return bytes(line)


def _parse_query(raw_path):
    if "?" not in raw_path:
        return raw_path, {}
    path, query = raw_path.split("?", 1)
    values = {}
    for item in query.split("&"):
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
        else:
            key, value = item, ""
        values[url_decode(key)] = url_decode(value)
    return path, values


def _send(client, status, content_type=b"text/plain", body=""):
    if isinstance(body, str):
        body = body.encode("utf-8")
    if isinstance(content_type, str):
        content_type = content_type.encode("utf-8")
    client.send(b"HTTP/1.1 " + status + b"\r\n")
    client.send(b"Connection: close\r\n")
    client.send(b"Content-Type: " + content_type + b"\r\n")
    client.send(b"Content-Length: " + str(len(body)).encode("utf-8") + b"\r\n\r\n")
    if body:
        client.send(body)


def _json(client, status, data):
    _send(client, status, b"application/json", json.dumps(data))


def _escape(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
