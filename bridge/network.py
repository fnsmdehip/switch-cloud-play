"""
Send controller input over the network.

Two use cases:
  1. Switch running sys-hidplus homebrew (accepts HID input over WiFi)
  2. Raspberry Pi on same network running NXBT (Bluetooth bridge)

Sends compact binary packets over UDP for minimal latency.
"""

import socket
import struct


class NetworkBridge:
    def __init__(self, host="192.168.1.100", port=8000):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set low-latency socket options
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)  # low delay
        self.sock.setblocking(False)
        print(f"    Network bridge: UDP → {self.host}:{self.port}")

    def send(self, switch_state):
        """Send Switch controller state over UDP."""
        if not self.sock:
            return
        packet = struct.pack(
            "BBBBBBBB",
            0xAB,
            (switch_state["buttons"] >> 8) & 0xFF,
            switch_state["buttons"] & 0xFF,
            switch_state["dpad"],
            switch_state["lx"],
            switch_state["ly"],
            switch_state["rx"],
            switch_state["ry"],
        )
        try:
            self.sock.sendto(packet, (self.host, self.port))
        except (BlockingIOError, OSError):
            pass

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None
