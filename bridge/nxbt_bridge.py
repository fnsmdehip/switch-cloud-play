"""
Send controller input to a Raspberry Pi running the NXBT bridge server.

The Pi runs nxbt_server.py (see scripts/nxbt_server.py), which:
  1. Receives UDP packets from this Mac client
  2. Translates them into NXBT Pro Controller commands
  3. Forwards to Switch via Bluetooth

This lets macOS users bypass the "Linux-only" limitation of NXBT.

Setup: Raspberry Pi 3/4/5 with Bluetooth, running nxbt_server.py.
"""

import socket
from input.mapper import SwitchMapper


class NXBTBridge:
    _packer = SwitchMapper()

    def __init__(self, host="192.168.1.200", port=9000):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)

        # Send a handshake to verify Pi is listening
        self.sock.sendto(b"HELLO", (self.host, self.port))
        print(f"    NXBT bridge: UDP -> {self.host}:{self.port}")
        print("    Make sure nxbt_server.py is running on your Raspberry Pi.")

    def send(self, switch_state):
        """Send Switch controller state to Pi."""
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
