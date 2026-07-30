import config

_logs = []


def log(component, message):
    line = "[{}] {}".format(component, message)
    _remember(line)
    if not getattr(config, "DEBUG_REPL", True):
        return
    try:
        print(line)
    except Exception:
        pass


def dump():
    for line in _logs:
        print(line)


def clear():
    _logs[:] = []


def _remember(line):
    _logs.append(line)
    limit = getattr(config, "DEBUG_BUFFER_SIZE", 50)
    while len(_logs) > limit:
        _logs.pop(0)
