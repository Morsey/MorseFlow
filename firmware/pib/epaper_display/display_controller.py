import gc
import os

import config
from debug import log
from epaper_display import BLACK, BUFFER_SIZE, EPD7in3F, WHITE


class DisplayController:
    def __init__(self):
        self.epd = EPD7in3F()
        self.current_image = None
        self.current_color = None
        self.busy = False
        self.pending = None
        self.last_error = None
        self.last_message = "booting"
        self.events = []
        self._ensure_image_dir()

    def init(self):
        self.epd.init()
        self.last_message = "ready"

    def queue_show(self, image):
        image = safe_image_name(image)
        self.pending = ("show", image)
        self.last_message = "queued {}".format(image)
        log("display", self.last_message)

    def queue_clear(self, color_name="white"):
        color_name = color_name.lower()
        if color_name not in ("white", "black"):
            raise ValueError("unsupported clear color")
        self.pending = ("color", color_name)
        self.last_message = "queued {}".format(color_name)
        log("display", self.last_message)

    def update(self, on_event=None):
        if self.busy or self.pending is None:
            return False
        action, value = self.pending
        self.pending = None
        self.busy = True
        self.last_error = None
        changed = True
        gc.collect()
        try:
            if action == "show":
                path = image_path(value)
                self.last_message = "displaying {}".format(value)
                log("display", self.last_message)
                self._emit("display", {"status": "started", "image": value}, on_event)
                self.epd.display_file(path)
                self.current_image = value
                self.current_color = None
                self.last_message = "displayed {}".format(value)
                self._emit("display", {"status": "complete", "image": value}, on_event)
            elif action == "color":
                color = WHITE if value == "white" else BLACK
                self.last_message = "displaying {}".format(value)
                log("display", self.last_message)
                self._emit("display", {"status": "started", "color": value}, on_event)
                self.epd.clear(color)
                self.current_image = None
                self.current_color = value
                self.last_message = "displayed {}".format(value)
                self._emit("display", {"status": "complete", "color": value}, on_event)
        except Exception as exc:
            self.last_error = repr(exc)
            self.last_message = "display failed: {}".format(self.last_error)
            self._emit("display", {"status": "error", "error": self.last_error}, on_event)
            log("display", self.last_message)
        finally:
            self.busy = False
            gc.collect()
        return changed

    def delete_image(self, image):
        image = safe_image_name(image)
        os.remove(image_path(image))
        if self.current_image == image:
            self.current_image = None
        self.last_message = "deleted {}".format(image)
        self.events.append(("file", {"status": "deleted", "image": image}))

    def state(self):
        pending = None
        if self.pending is not None:
            pending = {
                "action": self.pending[0],
                "value": self.pending[1],
            }
        return {
            "busy": self.busy,
            "pending": pending,
            "current_image": self.current_image,
            "current_color": self.current_color,
            "last_error": self.last_error,
            "last_message": self.last_message,
            "images": list_images(),
            "free_bytes": fs_free_bytes(),
        }

    def consume_events(self):
        events = self.events
        self.events = []
        return events

    def _emit(self, event_type, event_data, on_event):
        if on_event is not None:
            on_event(event_type, event_data)
        else:
            self.events.append((event_type, event_data))

    def _ensure_image_dir(self):
        try:
            os.mkdir(config.IMAGE_DIR)
        except OSError:
            pass


def safe_image_name(name):
    if isinstance(name, bytes):
        name = name.decode("utf-8")
    name = url_decode(str(name)).strip()
    if not name or "/" in name or "\\" in name or ".." in name:
        raise ValueError("bad image name")
    if not name.endswith(".bin"):
        raise ValueError("image must end with .bin")
    for char in name:
        if not (
            "0" <= char <= "9"
            or "A" <= char <= "Z"
            or "a" <= char <= "z"
            or char in " ._-"
        ):
            raise ValueError("bad image name")
    return name


def image_path(name):
    name = safe_image_name(name)
    path = "{}/{}".format(config.IMAGE_DIR, name)
    try:
        os.stat(path)
        return path
    except OSError:
        # Also support images uploaded to the root during manual testing.
        os.stat(name)
        return name


def upload_path(name):
    return "{}/{}".format(config.IMAGE_DIR, safe_image_name(name))


def list_images():
    images = []
    for directory in (config.IMAGE_DIR, "."):
        try:
            names = os.listdir(directory)
        except OSError:
            continue
        for name in names:
            if not name.endswith(".bin"):
                continue
            path = name if directory == "." else "{}/{}".format(directory, name)
            try:
                size = os.stat(path)[6]
            except OSError:
                continue
            images.append({"name": name, "size": size, "path": path})
    images.sort(key=lambda item: item["name"])
    return images


def fs_free_bytes():
    stat = os.statvfs("/")
    return stat[0] * stat[3]


def validate_image_size(path):
    size = os.stat(path)[6]
    if size != BUFFER_SIZE:
        raise ValueError("image file must be {} bytes".format(BUFFER_SIZE))


def url_decode(value):
    value = value.replace("+", " ")
    result = ""
    index = 0
    while index < len(value):
        if value[index] == "%" and index + 2 < len(value):
            try:
                result += chr(int(value[index + 1:index + 3], 16))
                index += 3
                continue
            except ValueError:
                pass
        result += value[index]
        index += 1
    return result
