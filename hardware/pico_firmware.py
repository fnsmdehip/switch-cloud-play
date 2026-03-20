"""
Raspberry Pi Pico firmware — acts as a USB Switch Pro Controller.

Flash this to a Raspberry Pi Pico (RP2040) using CircuitPython.
The Pico connects:
  - USB port A → Mac (receives serial commands)
  - USB port B (or GPIO) → Switch (emulates Pro Controller via USB HID)

For the Pico to appear as a Switch Pro Controller, it needs the
correct USB HID descriptor. This uses the adafruit_hid library.

SETUP:
  1. Install CircuitPython on Pico: https://circuitpython.org/board/raspberry_pi_pico/
  2. Copy this file as code.py to the CIRCUITPY drive
  3. Install libs: adafruit_hid

NOTE: The Switch Pro Controller USB HID descriptor is specific.
For a simpler approach, use the GP2040-CE firmware instead:
  https://gp2040-ce.info/
  - Flash GP2040-CE to a Pico
  - It natively appears as a Switch controller
  - Use the serial bridge mode to send commands from Mac

This file is a reference implementation. GP2040-CE is recommended
for production use as it handles all the USB descriptor details.
"""

# GP2040-CE is the recommended firmware for Pico → Switch controller.
# Download from: https://gp2040-ce.info/#/download
#
# After flashing GP2040-CE:
#   1. Hold BOOT button, connect Pico to Mac
#   2. Drag the GP2040-CE .uf2 file onto the RPI-RP2 drive
#   3. Connect Pico to Switch via USB
#   4. Pico appears as a gamepad to the Switch
#
# For serial bridge mode (controlled by Mac):
#   GP2040-CE supports a serial API. Connect a second Pico USB
#   or use UART pins to receive commands from the Mac.
#
# ALTERNATIVE: Use a Teensy LC/4.0 with the Switch-Fightstick firmware
#   https://github.com/progmem/Switch-Fightstick

# === CircuitPython reference (for custom builds) ===

REFERENCE_CODE = '''
import board
import busio
import struct
import usb_hid

# Switch Pro Controller HID report descriptor (simplified)
# Full implementation requires matching Nintendo's vendor/product IDs

uart = busio.UART(board.GP0, board.GP1, baudrate=115200, timeout=0.001)

# HID gamepad report
class SwitchReport:
    def __init__(self):
        self.buttons = 0
        self.dpad = 0x08  # center
        self.lx = 128
        self.ly = 128
        self.rx = 128
        self.ry = 128

    def to_bytes(self):
        return bytes([
            self.buttons & 0xFF,
            (self.buttons >> 8) & 0xFF,
            self.dpad,
            self.lx, self.ly,
            self.rx, self.ry,
            0x00,  # vendor
        ])

report = SwitchReport()
buf = bytearray(8)

while True:
    # Read 8-byte packet from Mac
    data = uart.read(8)
    if data and len(data) == 8 and data[0] == 0xAB:
        report.buttons = (data[1] << 8) | data[2]
        report.dpad = data[3]
        report.lx = data[4]
        report.ly = data[5]
        report.rx = data[6]
        report.ry = data[7]

        # Send HID report to Switch
        # (requires proper USB HID setup in boot.py)
        try:
            gamepad = usb_hid.devices[0]
            gamepad.send_report(report.to_bytes())
        except Exception:
            pass
'''
