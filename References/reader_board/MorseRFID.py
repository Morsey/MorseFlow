"""
Morse Immersive Technologies
Rob Morse
14 April 2026

MorseRFID reader board controller.

This script runs on the reader board. It uses a PN5180 NFC reader to detect a card UID,
updates a NeoPixel LED with status information, and exposes the latest card ID
to the controller over a two-wire GPIO link.

Version 1.2.0 - Two-wire status link without local known-card handling.

Copyright (c) 2026 Rob Morse

Permission is granted to copy, modify, and distribute this software for non-commercial use only.
Commercial sale or commercial redistribution is not permitted without prior written permission.
Licensed under Creative Commons Attribution-NonCommercial 4.0 International.
"""

from utime import sleep_ms, sleep_us, ticks_diff, ticks_ms
from machine import Pin
from neopixel import NeoPixel
from pn5180_morse import NFC
from two_wire_status import TwoWireStatusSlave, build_status_frame

try:
    import _thread
except ImportError:
    _thread = None

# Hardware pin assignments for this board.
# Change these values if your wiring is different.
NSS_PIN = 2
RST_PIN = 1
BSY_PIN = 3
# CARD_TYPE can be changed to ISO14443 if you are using ISO 14443 tags.
CARD_TYPE = "ISO14443"
#. CARD_TYPE = "ISO15693"
NEOPIXEL_PIN = 13       # NeoPixel data pin.
NEOPIXEL_COUNT = 1      # Number of NeoPixels connected.
PULSE_PIN = None        # Optional legacy 1 Hz heartbeat output pin.
TWO_WIRE_ENABLED = True
TWO_WIRE_CLK_PIN = 27   # Controller-driven clock line, idle high with pull-up.
TWO_WIRE_DATA_PIN = 26  # Shared open-drain data line, idle high with pull-up.
TWO_WIRE_BACKGROUND_SERVICE = True
TWO_WIRE_BIT_TIMEOUT_US = 20000
TWO_WIRE_THREAD_WAIT_US = 50000
ONBOARD_LED_ACTIVE_LOW = False  # Set True if board LED is turned on by 0 volts.
VERSION = "1.2.0"

# NeoPixel colors. The board uses a BGR-like channel order, so the values are
# arranged for the physical wiring of this NeoPixel board.
COLOR_OFF = (0, 0, 0)
COLOR_RUNNING = (0, 0, 8)        # Running/no card: dim blue on this board.
COLOR_CARD_PRESENT = (8, 0, 0)   # Card present: dim green on this board.
COLOR_ERROR = (0, 40, 0)         # Error: red color.

# Timing and card detection settings.
MISS_THRESHOLD = 3            # How many consecutive misses before we decide the card was removed.
SCAN_LOOP_SLEEP_MS = 5        # Short idle pause between PN5180 scans.
PRESENT_REPORT_MS = 1000       # Milliseconds between "card still present" messages.
CARD_TYPE_CODES = {
    "ISO14443": 1,
    "ISO15693": 2,
}
STATUS_FLAG_CARD_PRESENT = 0x01
STATUS_FLAG_READER_OK = 0x04
STATUS_FLAG_SCAN_ERROR = 0x08
ERROR_NONE = 0
ERROR_SCAN = 1


def init_onboard_led():
    """Initialize the board's built-in LED if available.

    Some boards provide a built-in LED with different pin names. This helper
    tries several common names until one succeeds.
    """
    for led_id in ("LED", 25, "GPIO25", "WL_GPIO0"):
        try:
            return Pin(led_id, Pin.OUT)
        except (TypeError, ValueError):
            pass
    return None


def set_onboard_led(led, on):
    """Turn the onboard LED on or off, handling inverted logic if needed."""
    if not led:
        return
    if ONBOARD_LED_ACTIVE_LOW:
        led.value(0 if on else 1)
    else:
        led.value(1 if on else 0)


def set_pixels(color):
    """Write the given color to all NeoPixel LEDs.

    NeoPixels require writing every pixel and then calling write() to update the strip.
    """
    for i in range(NEOPIXEL_COUNT):
        pixels[i] = color
    pixels.write()


def normal_status_color():
    """Return the steady LED color for the current reader state."""
    if last_error_code:
        return COLOR_ERROR
    if card_present:
        return COLOR_CARD_PRESENT
    return COLOR_RUNNING


def set_status_pixels(color):
    """Set the NeoPixel to the current steady status color."""
    set_pixels(color)


def refresh_status_led():
    """Restore the steady status color."""
    set_status_pixels(normal_status_color())


def service_two_wire(max_wait_us=0):
    """Allow the controller to poll the latest reader status."""
    if two_wire_thread_started:
        return
    if two_wire:
        try:
            two_wire.service(max_wait_us)
        except Exception as e:
            print("Two-wire link error:", e)


def two_wire_background_loop():
    """Continuously serve the controller link from the second RP2040 core."""
    while True:
        if not two_wire:
            sleep_ms(20)
            continue
        try:
            two_wire.service(TWO_WIRE_THREAD_WAIT_US)
        except Exception:
            sleep_ms(20)
        sleep_us(100)


def start_two_wire_background_service():
    """Start background servicing if the MicroPython build supports _thread."""
    global two_wire_thread_started
    if not TWO_WIRE_BACKGROUND_SERVICE or not two_wire or two_wire_thread_started:
        return
    if _thread is None:
        print("Two-wire background service unavailable; using main loop service.")
        return
    try:
        _thread.start_new_thread(two_wire_background_loop, ())
        two_wire_thread_started = True
        print("Two-wire background service started.")
    except Exception as e:
        print("Two-wire background service failed:", e)


def service_sleep_ms(total_ms):
    """Sleep in small chunks so the two-wire status link remains responsive."""
    remaining = total_ms
    while remaining > 0:
        service_two_wire(1000)
        step = 5 if remaining > 5 else remaining
        sleep_ms(step)
        remaining -= step


def toggle_pulse_outputs():
    """Toggle the pulse output pin and onboard LED state.

    This function makes the pulse pin toggle at 1 Hz (half-second on/off).
    It also mirrors the same state to the onboard LED if available.
    """
    global pulse_state
    pulse_state = 0 if pulse_state else 1
    if pulse_pin:
        pulse_pin.value(pulse_state)
    set_onboard_led(onboard_led, pulse_state)


def current_idle_color():
    """Return the idle NeoPixel color used while running with no card."""
    return COLOR_RUNNING


def update_idle_pulse(now_ms):
    """Keep the NeoPixel showing the running/no-card state when idle.

    When no card is present, the NeoPixel stays dim blue. This keeps the status
    LED from showing stale card colors while waiting for the next scan.
    """
    set_status_pixels(COLOR_RUNNING)


def invalid_response(value):
    """Treat empty or error-containing responses as invalid.

    Some PN5180 libraries return string values indicating an error instead of
    raising an exception. This helper checks for those cases.
    """
    text = str(value).lower()
    return not text or "error" in text


def make_status_frame():
    """Build the current RFID/card status in a fixed binary frame."""
    flags = STATUS_FLAG_READER_OK
    if card_present:
        flags |= STATUS_FLAG_CARD_PRESENT
    if last_error_code:
        flags |= STATUS_FLAG_SCAN_ERROR

    if last_status_change_ms:
        age_ms = ticks_diff(ticks_ms(), last_status_change_ms)
    else:
        age_ms = 0

    return build_status_frame(
        flags,
        status_sequence,
        age_ms,
        last_uid if card_present else None,
        1 if card_present and last_uid else 0,
        CARD_TYPE_CODES.get(CARD_TYPE, 0),
        last_error_code,
    )


def update_status_frame():
    """Refresh the cached status frame used by the two-wire responder."""
    global status_frame
    status_frame = make_status_frame()


def cached_status_frame():
    """Return a snapshot of the latest cached status frame.

    The two-wire responder may adjust command-specific fields, so it must get
    its own copy instead of the shared cached frame.
    """
    if status_frame is None:
        update_status_frame()
    return bytearray(status_frame)


# Initialize shared status before hardware setup so the controller can poll even
# while the PN5180 is starting or has failed.
two_wire = None
card_present = False
last_uid = None
last_error_code = ERROR_NONE
last_status_change_ms = ticks_ms()
status_sequence = 0
status_frame = None
two_wire_thread_started = False
update_status_frame()

if TWO_WIRE_ENABLED:
    two_wire = TwoWireStatusSlave(
        TWO_WIRE_CLK_PIN,
        TWO_WIRE_DATA_PIN,
        cached_status_frame,
        bit_timeout_us=TWO_WIRE_BIT_TIMEOUT_US,
    )

# Initialize the NeoPixel LED strip before any error handling may use it.
# This ensures the error path can light the NeoPixel even if the reader fails.
pixels = NeoPixel(Pin(NEOPIXEL_PIN, Pin.OUT), NEOPIXEL_COUNT)
reader = NFC(NSS_PIN, RST_PIN, BSY_PIN, card_reader_id="pn5180")
start_two_wire_background_service()

try:
    # Give the power supply a short time to settle before accessing hardware.
    # This helps when the board is powered independently instead of via USB.
    service_sleep_ms(100)

    # Start the PN5180 reader and query basic version strings.
    print("Initializing PN5180 reader...")
    reader.begin()
    service_sleep_ms(50)

    # Reset the reader so that it is in a known good state after power-up.
    if not reader.reset():
        raise ValueError("PN5180 reset failed")

    firmware = reader.get_firmware()
    if invalid_response(firmware):
        raise ValueError(f"Invalid firmware response: {firmware}")

    product = reader.get_product_version()
    if invalid_response(product):
        raise ValueError(f"Invalid product version response: {product}")

    eeprom = reader.get_eeprom_version()
    if invalid_response(eeprom):
        raise ValueError(f"Invalid EEPROM version response: {eeprom}")

    print("Firmware:", firmware)
    print("Product:", product)
    print("EEPROM:", eeprom)
except Exception as e:
    # If we cannot initialize the reader, show a red error LED and stop.
    print("Error connecting to PN5180:", e)
    last_error_code = ERROR_SCAN
    status_sequence = (status_sequence + 1) & 0xFF
    last_status_change_ms = ticks_ms()
    update_status_frame()
    set_pixels(COLOR_ERROR)
    while True:
        update_status_frame()
        service_sleep_ms(1000)  # Stay red indefinitely on connection error

# Initialize optional status outputs.
pulse_pin = Pin(PULSE_PIN, Pin.OUT) if PULSE_PIN is not None else None
onboard_led = init_onboard_led()

# Print startup status so the user can see what the board is doing.
print("PN5180 test starting...")
print(f"Reader mode: {CARD_TYPE}")
if two_wire:
    print(f"Two-wire status link: CLK={TWO_WIRE_CLK_PIN}, DATA={TWO_WIRE_DATA_PIN}")
if onboard_led:
    print("Onboard LED configured.")
else:
    print("Warning: onboard LED pin not found on this board.")
print("Present a card/tag to read UID.")

# Show that the reader firmware is running until a card is detected.
set_pixels(current_idle_color())

# Initialize pulse output and indicator pins.
pulse_state = 1
if pulse_pin:
    pulse_pin.value(pulse_state)
set_onboard_led(onboard_led, pulse_state)

miss_count = 0
last_present_report_ms = ticks_ms()
last_pulse_toggle_ms = ticks_ms()

try:
    while True:
        # Toggle the pulse output every 500 ms to create a heartbeat signal.
        if ticks_diff(ticks_ms(), last_pulse_toggle_ms) >= 500:
            toggle_pulse_outputs()
            last_pulse_toggle_ms = ticks_ms()

        update_status_frame()
        service_two_wire()

        # Try to read a card UID from the PN5180 reader.
        try:
            uid = reader.read_card_serial(CARD_TYPE)
            if last_error_code:
                last_error_code = ERROR_NONE
                status_sequence = (status_sequence + 1) & 0xFF
                last_status_change_ms = ticks_ms()
                update_status_frame()
        except Exception as e:
            # If the reader fails during scanning, show a red error briefly.
            print("Error reading card:", e)
            last_error_code = ERROR_SCAN
            status_sequence = (status_sequence + 1) & 0xFF
            last_status_change_ms = ticks_ms()
            update_status_frame()
            set_pixels(COLOR_ERROR)
            service_sleep_ms(1000)
            set_pixels(normal_status_color())
            service_sleep_ms(25)
            continue

        service_two_wire()

        if uid:
            # Card is currently present.
            miss_count = 0
            uid_hex = "".join("{:02X}".format(b) for b in uid)
            if uid_hex != last_uid:
                # New card detected. Update status and NeoPixel.
                print("Card UID:", uid_hex)
                print("Card present.")
                last_uid = uid_hex
                card_present = True
                status_sequence = (status_sequence + 1) & 0xFF
                last_status_change_ms = ticks_ms()
                update_status_frame()
                set_status_pixels(COLOR_CARD_PRESENT)
                last_present_report_ms = ticks_ms()
            elif card_present and ticks_diff(ticks_ms(), last_present_report_ms) >= PRESENT_REPORT_MS:
                # The same card is still present; report it periodically.
                print("Card still present:", uid_hex)
                set_status_pixels(COLOR_CARD_PRESENT)
                last_present_report_ms = ticks_ms()
        else:
            # No card read this loop. Count misses to avoid bouncing.
            miss_count += 1
            if miss_count >= MISS_THRESHOLD:
                if card_present:
                    print("Card removed.")
                last_uid = None
                card_present = False
                status_sequence = (status_sequence + 1) & 0xFF
                last_status_change_ms = ticks_ms()
                update_status_frame()
                set_status_pixels(COLOR_RUNNING)

        # Keep the status LED on the current steady state.
        if not card_present:
            update_idle_pulse(ticks_ms())
        else:
            refresh_status_led()

        update_status_frame()
        service_sleep_ms(SCAN_LOOP_SLEEP_MS)
except KeyboardInterrupt:
    # Clean up outputs when the script is stopped by the user.
    set_pixels(COLOR_OFF)
    if pulse_pin:
        pulse_pin.value(0)
    set_onboard_led(onboard_led, 0)
    print("Stopped PN5180 test.")
