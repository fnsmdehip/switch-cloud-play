"""
Send controller input to Switch via a microcontroller over serial.

The microcontroller (Arduino/Pico/Teensy) is connected:
  - USB to Mac (serial communication)
  - USB to Switch (emulates a Pro Controller)

The microcontroller runs firmware that receives our binary packets
and translates them into USB HID reports the Switch understands.

See hardware/pico_firmware.py for the Raspberry Pi Pico firmware.
"""

import struct
import serial


class SerialBridge:
    def __init__(self, port="/dev/tty.usbmodem1101", baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None

    def connect(self):
        self.serial = serial.Serial(
            self.port,
            self.baud_rate,
            timeout=0.01,
            write_timeout=0.01,
        )
        # Wait for microcontroller to reset
        import time
        time.sleep(0.5)
        # Flush any startup messages
        self.serial.reset_input_buffer()
        print(f"    Serial connected: {self.port} @ {self.baud_rate}")

    def send(self, switch_state):
        """Send a Switch controller state packet over serial."""
        if not self.serial or not self.serial.is_open:
            return
        packet = struct.pack(
            "BBBBBBBB",
            0xAB,  # sync byte
            (switch_state["buttons"] >> 8) & 0xFF,
            switch_state["buttons"] & 0xFF,
            switch_state["dpad"],
            switch_state["lx"],
            switch_state["ly"],
            switch_state["rx"],
            switch_state["ry"],
        )
        try:
            self.serial.write(packet)
        except serial.SerialTimeoutException:
            pass

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
