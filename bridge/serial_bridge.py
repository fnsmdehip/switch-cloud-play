"""
Send controller input to Switch via a microcontroller over serial.

The microcontroller (Arduino/Pico/Teensy) is connected:
  - USB to Mac (serial communication)
  - USB to Switch (emulates a Pro Controller)

The microcontroller runs firmware that receives our binary packets
and translates them into USB HID reports the Switch understands.

See hardware/pico_firmware.py for the Raspberry Pi Pico firmware.
"""

import time
import serial
from input.mapper import SwitchMapper


class SerialBridge:
    _packer = SwitchMapper()

    def __init__(self, port="auto", baud_rate=115200):
        self.port = port
        self.baud_rate = baud_rate
        self.serial = None

    def _find_serial_port(self):
        """Auto-detect serial port for microcontroller on macOS."""
        import glob
        candidates = glob.glob("/dev/tty.usbmodem*") + glob.glob("/dev/tty.usbserial*")
        if candidates:
            print(f"    Found serial ports: {candidates}")
            return candidates[0]
        raise RuntimeError(
            "No serial device found. Connect your Pico/Arduino via USB.\n"
            "    Expected: /dev/tty.usbmodem* or /dev/tty.usbserial*"
        )

    def connect(self):
        if self.port == "auto":
            self.port = self._find_serial_port()

        self.serial = serial.Serial(
            self.port,
            self.baud_rate,
            timeout=0.01,
            write_timeout=0.01,
        )
        # Wait for microcontroller to reset
        time.sleep(0.5)
        # Flush any startup messages
        self.serial.reset_input_buffer()
        print(f"    Serial connected: {self.port} @ {self.baud_rate}")

    def send(self, switch_state):
        """Send a Switch controller state packet over serial."""
        if not self.serial or not self.serial.is_open:
            return
        try:
            self.serial.write(self._packer.to_bytes(switch_state))
        except serial.SerialTimeoutException:
            pass

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
