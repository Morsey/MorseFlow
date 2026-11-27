__version__ = "1.0.0"

# Keep each device module's version on its first line. Bump the corresponding
# entry here when changing that module, and bump this manifest's version.
EXPECTED = dict.fromkeys(
    "app boot config debug display_controller epaper_display ethernet http_service "
    "main messages mqtt_client mqtt_service onboard_led test_display "
    "test_network_mqtt versions".split(), "1.0.0"
)
DISPLAY = "config debug display_controller epaper_display test_display versions".split()
NETWORK = "config debug ethernet messages mqtt_client test_network_mqtt versions".split()
RUNTIME = [name for name in EXPECTED if not name.startswith("test_")]


def report(names=None):
    print("E-paper PIB upload manifest", __version__)
    ok = True
    for name in sorted(EXPECTED if names is None else names):
        path = name + ".py"
        try:
            with open(path) as source:
                line = source.readline().strip()
            prefix = '__version__ = "'
            actual = line[len(prefix):-1] if line.startswith(prefix) and line.endswith('"') else "UNVERSIONED"
        except OSError:
            actual = "MISSING"
        expected = EXPECTED[name]
        matches = actual == expected
        print("{}  {}  {}".format(path, actual, "OK" if matches else "expected " + expected))
        ok = ok and matches
    print("Upload check:", "PASS" if ok else "CHECK FILES")
    return ok
