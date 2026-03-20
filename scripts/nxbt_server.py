#!/usr/bin/env python3
"""
NXBT Bridge Server — runs on a Raspberry Pi.

Receives UDP packets from the Mac client and translates them into
NXBT Pro Controller commands sent to the Switch over Bluetooth.

Requirements (on Pi):
    pip install nxbt

Usage:
    python nxbt_server.py

The Pi must be paired with the Switch (open "Change Grip/Order" on Switch first).
"""

import socket
import struct
import time
import sys

try:
    import nxbt
except ImportError:
    print("Error: nxbt not installed. Run: pip install nxbt")
    sys.exit(1)

HOST = "0.0.0.0"
PORT = 9000

# Switch button constants matching our protocol
BTN_Y       = 0x0001
BTN_B       = 0x0002
BTN_A       = 0x0004
BTN_X       = 0x0008
BTN_L       = 0x0010
BTN_R       = 0x0020
BTN_ZL      = 0x0040
BTN_ZR      = 0x0080
BTN_MINUS   = 0x0100
BTN_PLUS    = 0x0200
BTN_LSTICK  = 0x0400
BTN_RSTICK  = 0x0800
BTN_HOME    = 0x1000
BTN_CAPTURE = 0x2000

DPAD_NAMES = {
    0x00: None,
    0x01: nxbt.Buttons.DPAD_UP,
    0x03: nxbt.Buttons.DPAD_RIGHT,
    0x05: nxbt.Buttons.DPAD_DOWN,
    0x07: nxbt.Buttons.DPAD_LEFT,
}

BUTTON_MAP = {
    BTN_A: nxbt.Buttons.A,
    BTN_B: nxbt.Buttons.B,
    BTN_X: nxbt.Buttons.X,
    BTN_Y: nxbt.Buttons.Y,
    BTN_L: nxbt.Buttons.L,
    BTN_R: nxbt.Buttons.R,
    BTN_ZL: nxbt.Buttons.ZL,
    BTN_ZR: nxbt.Buttons.ZR,
    BTN_MINUS: nxbt.Buttons.MINUS,
    BTN_PLUS: nxbt.Buttons.PLUS,
    BTN_LSTICK: nxbt.Buttons.L_STICK_PRESS,
    BTN_RSTICK: nxbt.Buttons.R_STICK_PRESS,
    BTN_HOME: nxbt.Buttons.HOME,
    BTN_CAPTURE: nxbt.Buttons.CAPTURE,
}


def main():
    print(f"[*] Starting NXBT bridge server on port {PORT}")
    print("[*] Initializing NXBT...")

    nx = nxbt.Nxbt()

    print("[*] Creating Pro Controller...")
    print("[!] Open 'Change Grip/Order' on your Switch NOW!")

    controller_idx = nx.create_controller(nxbt.PRO_CONTROLLER)
    nx.wait_for_connection(controller_idx)
    print("[+] Controller connected to Switch!")

    # UDP server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    sock.settimeout(0.001)
    print(f"[+] Listening for input on UDP {HOST}:{PORT}")

    prev_buttons = 0

    while True:
        try:
            data, addr = sock.recvfrom(16)
        except socket.timeout:
            continue

        if data == b"HELLO":
            sock.sendto(b"OK", addr)
            continue

        if len(data) < 8 or data[0] != 0xAB:
            continue

        _, btn_hi, btn_lo, dpad, lx, ly, rx, ry = struct.unpack("BBBBBBBB", data[:8])
        buttons = (btn_hi << 8) | btn_lo

        # Convert stick values from 0-255 to -100..100 for NXBT
        lx_nxbt = int((lx - 128) * 100 / 127)
        ly_nxbt = int((ly - 128) * 100 / 127)
        rx_nxbt = int((rx - 128) * 100 / 127)
        ry_nxbt = int((ry - 128) * 100 / 127)

        # Set sticks
        nx.set_stick(controller_idx, nxbt.Sticks.LEFT_STICK, lx_nxbt, ly_nxbt)
        nx.set_stick(controller_idx, nxbt.Sticks.RIGHT_STICK, rx_nxbt, ry_nxbt)

        # Handle button presses/releases
        for bit, nxbt_btn in BUTTON_MAP.items():
            pressed_now = bool(buttons & bit)
            pressed_before = bool(prev_buttons & bit)
            if pressed_now and not pressed_before:
                nx.press_buttons(controller_idx, [nxbt_btn])
            elif not pressed_now and pressed_before:
                nx.release_buttons(controller_idx, [nxbt_btn])

        # Handle D-pad
        dpad_btn = DPAD_NAMES.get(dpad)
        if dpad_btn:
            nx.press_buttons(controller_idx, [dpad_btn])

        prev_buttons = buttons


if __name__ == "__main__":
    main()
