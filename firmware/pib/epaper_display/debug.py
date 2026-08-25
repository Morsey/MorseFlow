import config


_buffer = []


def log(source, message):
    line = "[{}] {}".format(source, message)
    _buffer.append(line)
    if len(_buffer) > config.DEBUG_BUFFER_SIZE:
        _buffer.pop(0)
    if config.DEBUG_REPL:
        print(line)


def dump():
    for line in _buffer:
        print(line)


def clear():
    _buffer[:] = []
