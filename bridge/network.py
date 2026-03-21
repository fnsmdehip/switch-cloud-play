"""
Send controller input over the network.

Two use cases:
  1. Switch running sys-hidplus homebrew (accepts HID input over WiFi)
  2. Raspberry Pi on same network running NXBT (Bluetooth bridge)

Sends compact binary packets over UDP for minimal latency.
"""

import socket
from input.mapper import SwitchMapper


class NetworkBridge:
    _packer = SwitchMapper()

    def __init__(self, host="192.168.1.100", port=8000):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set low-latency socket options
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)  # low delay
        self.sock.setblocking(False)
        print(f"    Network bridge: UDP -> {self.host}:{self.port}")

    def send(self, switch_state):
        """Send Switch controller state over UDP."""
        if not self.sock:
            return
        try:
            self.sock.sendto(self._packer.to_bytes(switch_state), (self.host, self.port))
        except (BlockingIOError, OSError):
            pass

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None
