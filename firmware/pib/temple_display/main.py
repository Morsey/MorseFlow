"""Pico W controller for a MedeaWiz Sprite 4K video player."""

import gc
import socket
import time

import network
from machine import Pin, UART

try:
    import ujson as json
except ImportError:
    import json


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WIFI_SSID = "CHANGE_ME"
WIFI_PASSWORD = "CHANGE_ME"
HOSTNAME = "temple-display"

# Sprite 4K serial control. UART0 on GP0/GP1 is used by default.
SPRITE_UART_ID = 0
SPRITE_TX_PIN = 0
SPRITE_RX_PIN = 1
SPRITE_BAUDRATE = 9600

# Set to 0xE1 through 0xEF only if Sprite Address Mode is enabled. Leave as
# None for the normal single-player connection.
SPRITE_ADDRESS = None

# Each button connects its GPIO to GND when pressed. Internal pull-ups are used.
BUTTON_ACTIONS = {
    10: ("play", 0),
    11: ("play", 1),
    12: ("play", 2),
    13: ("play", 3),
    14: ("pause_resume", None),
    15: ("stop", None),
}
BUTTON_DEBOUNCE_MS = 50

# File controls shown on the website.
WEB_FILES = (0, 1, 2, 3)

HTTP_PORT = 80
WIFI_RETRY_MS = 10000
STATUS_LED_PIN = "LED"
FEEDBACK_HISTORY_SIZE = 10
# Delay before running the one-time serial connection check.
STARTUP_TEST_DELAY_MS = 3000
STARTUP_TEST_TIMEOUT_MS = 3000


class SpritePlayer:
    """Send the Sprite 4K's one-byte TTL serial commands."""

    SLEEP = 0xC9
    WAKE = 0xCA
    REQUEST_FILE_COUNT = 0xCB
    REQUEST_CURRENT_FILE = 0xCC
    PLAY_RESUME = 0xEF
    PAUSE = 0xF0

    def __init__(self):
        self.uart = UART(
            SPRITE_UART_ID,
            baudrate=SPRITE_BAUDRATE,
            bits=8,
            parity=None,
            stop=1,
            tx=Pin(SPRITE_TX_PIN),
            rx=Pin(SPRITE_RX_PIN),
        )
        self.last_command = None
        self.last_feedback = b""
        self.feedback_history = []
        self.connection_test = {
            "status": "waiting",
            "message": "Startup serial test has not run yet",
        }
        self.connection_test_started_ms = None
        self.paused = False
        self.stopped = False

    def play(self, file_number):
        file_number = int(file_number)
        if not 0 <= file_number <= 200:
            raise ValueError("Sprite file number must be between 0 and 200")
        if self.stopped:
            self.wake()
        self._send(file_number)
        self.paused = False
        self.stopped = False

    def sleep(self):
        self._send(self.SLEEP)
        self.paused = False
        self.stopped = True

    def wake(self):
        self._send(self.WAKE)
        self.stopped = False

    def pause_resume(self):
        if self.stopped:
            self.wake()
            self.paused = False
        elif self.paused:
            self._send(self.PLAY_RESUME)
            self.paused = False
        else:
            self._send(self.PAUSE)
            self.paused = True

    def request_current_file(self):
        self._send(self.REQUEST_CURRENT_FILE)

    def start_connection_test(self, now_ms):
        print("Sprite connection test: requesting current file")
        self.connection_test = {
            "status": "pending",
            "message": "Waiting for Sprite serial feedback",
        }
        self.connection_test_started_ms = now_ms
        self.request_current_file()

    def update(self, now_ms):
        waiting = self.uart.any()
        if waiting:
            self.last_feedback = self.uart.read(waiting) or b""
            for value in self.last_feedback:
                item = {
                    "value": value,
                    "hex": "0x{:02X}".format(value),
                    "meaning": self._feedback_meaning(value),
                    "timestamp": _timestamp(),
                }
                self.feedback_history.append(item)
                if len(self.feedback_history) > FEEDBACK_HISTORY_SIZE:
                    self.feedback_history.pop(0)
                print(
                    "Sprite feedback [{}]: {} ({})".format(
                        item["timestamp"],
                        item["meaning"],
                        item["hex"],
                    )
                )
            if self.connection_test["status"] == "pending":
                self.connection_test = {
                    "status": "passed",
                    "message": "Sprite replied over serial",
                }
                print("Sprite connection test: PASSED")

        if (
            self.connection_test["status"] == "pending"
            and time.ticks_diff(now_ms, self.connection_test_started_ms)
            >= STARTUP_TEST_TIMEOUT_MS
        ):
            self.connection_test = {
                "status": "failed",
                "message": "No serial feedback received before timeout",
            }
            print(
                "Sprite connection test: FAILED - check RX/TX wiring, common "
                "ground, baud rate, and the Sprite Serial Feedback setting"
            )

    def _send(self, command):
        command = int(command)
        payload = bytes((command,))
        address = SPRITE_ADDRESS
        if address is not None:
            payload = bytes((int(address), command))
        bytes_written = self.uart.write(payload)
        self.last_command = command
        print(
            "Sprite TX: {} command={} bytes_written={}".format(
                " ".join("{:02X}".format(value) for value in payload),
                command,
                bytes_written,
            )
        )

    @staticmethod
    def _feedback_meaning(value):
        if 0 <= value <= 200:
            return "Player reports file {:03d} is playing".format(value)
        meanings = {
            SpritePlayer.SLEEP: "Player acknowledged the sleep command",
            SpritePlayer.WAKE: "Player acknowledged the wake command",
            SpritePlayer.REQUEST_FILE_COUNT: "Player echoed the file-count request",
            SpritePlayer.REQUEST_CURRENT_FILE: "Player echoed the current-file request",
            0xEE: "Player reports the end of a file",
            SpritePlayer.PLAY_RESUME: "Player acknowledged play/resume",
            SpritePlayer.PAUSE: "Player acknowledged pause",
        }
        return meanings.get(value, "Player returned an unknown value")

    def status(self):
        return {
            "ok": True,
            "last_command": self.last_command,
            "paused": self.paused,
            "stopped": self.stopped,
            "last_feedback_hex": " ".join(
                "{:02X}".format(value) for value in self.last_feedback
            ),
            "connection_test": self.connection_test,
            "feedback": self.feedback_history,
        }


class Button:
    def __init__(self, gpio, action, argument=None):
        self.pin = Pin(gpio, Pin.IN, Pin.PULL_UP)
        self.gpio = gpio
        self.action = action
        self.argument = argument
        self.stable_value = self.pin.value()
        self.candidate_value = self.stable_value
        self.changed_at = time.ticks_ms()

    def update(self, now_ms):
        value = self.pin.value()
        if value != self.candidate_value:
            self.candidate_value = value
            self.changed_at = now_ms
            return False
        if value != self.stable_value and time.ticks_diff(now_ms, self.changed_at) >= BUTTON_DEBOUNCE_MS:
            self.stable_value = value
            return value == 0
        return False


class WebServer:
    def __init__(self, player):
        self.player = player
        self.server = None

    def start(self):
        address = socket.getaddrinfo("0.0.0.0", HTTP_PORT)[0][-1]
        server = socket.socket()
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(address)
        server.listen(2)
        server.setblocking(False)
        self.server = server
        print("HTTP server listening on port", HTTP_PORT)

    def update(self):
        if self.server is None:
            return
        try:
            connection, _ = self.server.accept()
        except OSError:
            return
        try:
            # Browsers may open a connection before sending the request. Give
            # them a little time, but keep the pause short enough that the
            # physical buttons remain responsive.
            connection.settimeout(0.5)
            request = connection.recv(1024)
            if not request:
                return
            self._handle(connection, request)
        except OSError as exc:
            # ETIMEDOUT is normal for speculative/preconnected browser sockets.
            if not exc.args or exc.args[0] != 110:
                print("HTTP socket failed:", repr(exc))
        except Exception as exc:
            print("HTTP request failed:", repr(exc))
            try:
                self._respond(connection, "500 Internal Server Error", "text/plain", "Request failed")
            except OSError:
                pass
        finally:
            connection.close()

    def _handle(self, connection, request):
        try:
            request_line = request.split(b"\r\n", 1)[0].decode()
            _method, target, _version = request_line.split(" ", 2)
        except Exception:
            self._respond(connection, "400 Bad Request", "text/plain", "Bad request")
            return

        path, _, query = target.partition("?")
        parameters = self._query_parameters(query)
        print("HTTP {} {}".format(_method, target))

        if path == "/api/play":
            try:
                file_number = int(parameters["file"])
                if file_number not in WEB_FILES:
                    raise ValueError
                self.player.play(file_number)
            except (KeyError, ValueError):
                self._respond(connection, "400 Bad Request", "application/json", '{"ok":false,"error":"file must be 0, 1, 2, or 3"}')
                return
            self._respond(connection, "200 OK", "application/json", '{{"ok":true,"file":{}}}'.format(file_number))
        elif path == "/api/sleep":
            self.player.sleep()
            self._respond(connection, "200 OK", "application/json", '{"ok":true}')
        elif path == "/api/stop":
            self.player.sleep()
            self._respond(connection, "200 OK", "application/json", '{"ok":true,"stopped":true}')
        elif path == "/api/wake":
            self.player.wake()
            self._respond(connection, "200 OK", "application/json", '{"ok":true}')
        elif path == "/api/pause-resume":
            self.player.pause_resume()
            self._respond(
                connection,
                "200 OK",
                "application/json",
                json.dumps({"ok": True, "paused": self.player.paused}),
            )
        elif path == "/api/help":
            self._respond(
                connection,
                "200 OK",
                "application/json",
                json.dumps(self._api_description()),
            )
        elif path == "/api/status":
            self._respond(
                connection,
                "200 OK",
                "application/json",
                json.dumps(self.player.status()),
            )
        elif path == "/" or path == "/index.html":
            self._respond(connection, "200 OK", "text/html", self._page())
        else:
            self._respond(connection, "404 Not Found", "text/plain", "Not found")

    @staticmethod
    def _api_description():
        return {
            "name": "Temple Display Sprite Controller",
            "instructions": "Use HTTP POST requests to control the video player. No request body is required.",
            "endpoints": {
                "play": "POST /api/play?file=0 where file is 0, 1, 2, or 3",
                "pause_resume": "POST /api/pause-resume",
                "stop_blank": "POST /api/stop",
                "status": "GET /api/status",
                "help": "GET /api/help",
            },
        }

    @staticmethod
    def _query_parameters(query):
        result = {}
        for part in query.split("&"):
            key, separator, value = part.partition("=")
            if separator:
                result[key] = value
        return result

    @staticmethod
    def _respond(connection, status, content_type, body):
        body = body.encode()
        headers = (
            "HTTP/1.0 {}\r\nContent-Type: {}; charset=utf-8\r\n"
            "Content-Length: {}\r\nCache-Control: no-store\r\n"
            "Connection: close\r\n\r\n"
        ).format(status, content_type, len(body))
        connection.sendall(headers.encode() + body)

    @staticmethod
    def _page():
        buttons = "".join(
            '<button onclick="play({0})">Play {0:03d}</button>'.format(file_number)
            for file_number in WEB_FILES
        )
        page = """<!doctype html>
<html><head><meta name="viewport" content="width=device-width"><title>Temple Display</title>
<style>body{font:18px sans-serif;max-width:36rem;margin:2rem auto;padding:0 1rem}button,input{font:inherit;margin:.35rem;padding:.7rem}#status{margin-top:1rem}</style></head>
<body><h1>Temple Display</h1><div>BUTTONS_HTML</div>
<p><button type="button" onclick="sendControl('pause-resume')">Pause / Resume</button><button type="button" onclick="sendControl('stop')">Stop / Blank</button></p>
<div id="status"></div><h2>Serial feedback</h2><pre id="feedback">Waiting for feedback...</pre>
<details><summary>Automation API</summary><pre>POST /api/play?file=0
POST /api/pause-resume
POST /api/stop
GET /api/status
GET /api/help</pre></details>
<script type="application/json" id="ai-control-api">{"description":"Control the Temple Display with HTTP","help":"GET /api/help","play":"POST /api/play?file={0|1|2|3}","pause_resume":"POST /api/pause-resume","stop_blank":"POST /api/stop","status":"GET /api/status"}</script>
<script>
const statusElement=document.getElementById('status');
const feedbackElement=document.getElementById('feedback');
async function play(n){try{let r=await fetch('/api/play?file='+n,{method:'POST'});if(!r.ok)throw new Error(await r.text());await refresh()}catch(e){statusElement.textContent='Play failed: '+e}}
async function sendControl(action){statusElement.textContent='Sending '+action+'...';try{let r=await fetch('/api/'+action,{method:'POST',cache:'no-store'});if(!r.ok)throw new Error(await r.text());statusElement.textContent=action+' sent';await refresh()}catch(e){statusElement.textContent='Command failed: '+e}}
async function refresh(){try{let r=await fetch('/api/status',{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);let s=await r.json();statusElement.textContent='Connection test: '+s.connection_test.status+' - '+s.connection_test.message+' | Last command: '+(s.last_command===null?'none':s.last_command);feedbackElement.textContent=s.feedback.length?s.feedback.slice().reverse().map(x=>x.timestamp+'  '+x.meaning).join('\\n'):'Waiting for feedback...'}catch(e){statusElement.textContent='Status unavailable: '+e}}
refresh();setInterval(refresh,2000);
</script></body></html>"""
        return page.replace("BUTTONS_HTML", buttons)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    try:
        network.hostname(HOSTNAME)
    except Exception:
        pass
    if not wlan.isconnected():
        print("Connecting to Wi-Fi", WIFI_SSID)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    return wlan


def _timestamp():
    current = time.localtime()
    if current[0] >= 2024:
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d} UTC".format(
            current[0], current[1], current[2], current[3], current[4], current[5]
        )
    uptime_ms = time.ticks_ms()
    return "+{}.{:03d}s uptime".format(uptime_ms // 1000, uptime_ms % 1000)


def main():
    led = Pin(STATUS_LED_PIN, Pin.OUT)
    player = SpritePlayer()
    buttons = [
        Button(gpio, action, argument)
        for gpio, (action, argument) in BUTTON_ACTIONS.items()
    ]
    wlan = connect_wifi()
    web = WebServer(player)
    startup_test_at = time.ticks_add(time.ticks_ms(), STARTUP_TEST_DELAY_MS)
    startup_test_started = False
    next_wifi_retry = time.ticks_add(time.ticks_ms(), WIFI_RETRY_MS)
    announced_ip = None
    clock_sync_attempted = False

    while True:
        now_ms = time.ticks_ms()
        if not startup_test_started and time.ticks_diff(now_ms, startup_test_at) >= 0:
            startup_test_started = True
            player.start_connection_test(now_ms)
        player.update(now_ms)
        for button in buttons:
            if button.update(now_ms):
                print("Button GP{} -> {} {}".format(button.gpio, button.action, button.argument))
                if button.action == "play":
                    player.play(button.argument)
                elif button.action == "pause_resume":
                    player.pause_resume()
                elif button.action == "stop":
                    player.sleep()

        if wlan.isconnected():
            ip_address = wlan.ifconfig()[0]
            led.value(1)
            if ip_address != announced_ip:
                announced_ip = ip_address
                print("Temple Display available at http://{}/".format(ip_address))
            if not clock_sync_attempted:
                clock_sync_attempted = True
                try:
                    import ntptime

                    ntptime.settime()
                    print("Clock synchronized by NTP (UTC)")
                except Exception as exc:
                    print("NTP clock synchronization failed:", repr(exc))
            if web.server is None:
                web.start()
            web.update()
        else:
            led.value((now_ms // 250) % 2)
            if time.ticks_diff(now_ms, next_wifi_retry) >= 0:
                print("Wi-Fi disconnected; reconnecting")
                wlan.connect(WIFI_SSID, WIFI_PASSWORD)
                next_wifi_retry = time.ticks_add(now_ms, WIFI_RETRY_MS)

        gc.collect()
        time.sleep_ms(10)


if __name__ == "__main__":
    main()
