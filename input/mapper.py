"""
Map generic gamepad input to Nintendo Switch Pro Controller format.

Switch Pro Controller layout:
  Buttons: A, B, X, Y, L, R, ZL, ZR, Plus, Minus, Home, Capture,
           L-Stick click, R-Stick click
  Sticks:  Left (x,y), Right (x,y)
  D-pad:   Up, Down, Left, Right

The button indices vary by controller brand (Xbox, PS, etc).
This mapper handles common layouts.
"""

import struct

# Standard SDL/pygame button indices for common controllers
# These map well for Xbox controllers on macOS
XBOX_MAP = {
    "a": 0,        # A (Xbox) → B (Switch) — note: Nintendo swaps A/B
    "b": 1,        # B (Xbox) → A (Switch)
    "x": 2,        # X (Xbox) → Y (Switch)
    "y": 3,        # Y (Xbox) → X (Switch)
    "lb": 4,       # LB → L
    "rb": 5,       # RB → R
    "back": 6,     # Back/Select → Minus
    "start": 7,    # Start/Menu → Plus
    "lstick": 8,   # L-Stick click
    "rstick": 9,   # R-Stick click
    "guide": 10,   # Guide → Home
}

# Switch button bit flags for the serial protocol
SWITCH_BTN = {
    "y":       0x0001,
    "b":       0x0002,
    "a":       0x0004,
    "x":       0x0008,
    "l":       0x0010,
    "r":       0x0020,
    "zl":      0x0040,
    "zr":      0x0080,
    "minus":   0x0100,
    "plus":    0x0200,
    "lstick":  0x0400,
    "rstick":  0x0800,
    "home":    0x1000,
    "capture": 0x2000,
}

DPAD_MAP = {
    (0, 0):   0x00,  # center
    (0, 1):   0x01,  # up
    (1, 1):   0x02,  # up-right
    (1, 0):   0x03,  # right
    (1, -1):  0x04,  # down-right
    (0, -1):  0x05,  # down
    (-1, -1): 0x06,  # down-left
    (-1, 0):  0x07,  # left
    (-1, 1):  0x08,  # up-left
}


PS_MAP = {
    "cross": 0,     # Cross (PS) -> B (Switch)
    "circle": 1,    # Circle (PS) -> A (Switch)
    "square": 2,    # Square (PS) -> Y (Switch)
    "triangle": 3,  # Triangle (PS) -> X (Switch)
    "l1": 4,        # L1 -> L
    "r1": 5,        # R1 -> R
    "share": 6,     # Share -> Minus
    "options": 7,   # Options -> Plus
    "lstick": 8,    # L-Stick click
    "rstick": 9,    # R-Stick click
    "ps": 10,       # PS button -> Home
}


class SwitchMapper:
    def __init__(self, layout="auto"):
        self.layout = layout

    def _detect_layout(self, controller_name):
        """Guess controller layout from pygame's reported name."""
        name = (controller_name or "").lower()
        if "dualshock" in name or "dualsense" in name or "ps4" in name or "ps5" in name or "sony" in name:
            return "ps"
        return "xbox"

    def map(self, raw, controller_name=None):
        """Convert raw gamepad state to Switch controller packet.

        Auto-detects Xbox vs PS layout from controller_name on first call.
        Both use the same SDL button indices on macOS; the difference is
        which face buttons map to which Switch buttons.
        """
        buttons = raw.get("buttons", [])

        def btn(idx):
            return buttons[idx] if idx < len(buttons) else 0

        # Pick layout (Xbox and PS have same SDL indices on macOS,
        # but face button semantics differ — PS Cross=bottom like Switch B)
        layout = self.layout
        if layout == "auto":
            layout = self._detect_layout(controller_name)

        # Build button bitmask
        if layout == "ps":
            # PS: Cross(0)=B, Circle(1)=A, Square(2)=Y, Triangle(3)=X
            btn_mask = 0
            if btn(PS_MAP["cross"]):    btn_mask |= SWITCH_BTN["b"]
            if btn(PS_MAP["circle"]):   btn_mask |= SWITCH_BTN["a"]
            if btn(PS_MAP["square"]):   btn_mask |= SWITCH_BTN["y"]
            if btn(PS_MAP["triangle"]): btn_mask |= SWITCH_BTN["x"]
            if btn(PS_MAP["l1"]):       btn_mask |= SWITCH_BTN["l"]
            if btn(PS_MAP["r1"]):       btn_mask |= SWITCH_BTN["r"]
            if btn(PS_MAP["share"]):    btn_mask |= SWITCH_BTN["minus"]
            if btn(PS_MAP["options"]):  btn_mask |= SWITCH_BTN["plus"]
            if btn(PS_MAP["lstick"]):   btn_mask |= SWITCH_BTN["lstick"]
            if btn(PS_MAP["rstick"]):   btn_mask |= SWITCH_BTN["rstick"]
            if btn(PS_MAP["ps"]):       btn_mask |= SWITCH_BTN["home"]
        else:
            # Xbox: A(0)=B, B(1)=A, X(2)=Y, Y(3)=X (Nintendo A/B X/Y swap)
            btn_mask = 0
            if btn(XBOX_MAP["a"]):     btn_mask |= SWITCH_BTN["b"]
            if btn(XBOX_MAP["b"]):     btn_mask |= SWITCH_BTN["a"]
            if btn(XBOX_MAP["x"]):     btn_mask |= SWITCH_BTN["y"]
            if btn(XBOX_MAP["y"]):     btn_mask |= SWITCH_BTN["x"]
            if btn(XBOX_MAP["lb"]):    btn_mask |= SWITCH_BTN["l"]
            if btn(XBOX_MAP["rb"]):    btn_mask |= SWITCH_BTN["r"]
            if btn(XBOX_MAP["back"]):  btn_mask |= SWITCH_BTN["minus"]
            if btn(XBOX_MAP["start"]): btn_mask |= SWITCH_BTN["plus"]
            if btn(XBOX_MAP["lstick"]):btn_mask |= SWITCH_BTN["lstick"]
            if btn(XBOX_MAP["rstick"]):btn_mask |= SWITCH_BTN["rstick"]
            if btn(XBOX_MAP["guide"]): btn_mask |= SWITCH_BTN["home"]

        # Triggers → ZL/ZR (analog triggers treated as digital)
        if raw.get("left_trigger", 0) > 0.5:
            btn_mask |= SWITCH_BTN["zl"]
        if raw.get("right_trigger", 0) > 0.5:
            btn_mask |= SWITCH_BTN["zr"]

        # D-pad
        dpad = raw.get("dpad", (0, 0))
        dpad_val = DPAD_MAP.get(dpad, 0x00)

        # Sticks: convert from -1.0..1.0 to 0..255 (128 = center)
        lx = int((raw.get("left_stick_x", 0) + 1.0) * 127.5)
        ly = int((-raw.get("left_stick_y", 0) + 1.0) * 127.5)  # invert Y
        rx = int((raw.get("right_stick_x", 0) + 1.0) * 127.5)
        ry = int((-raw.get("right_stick_y", 0) + 1.0) * 127.5)

        # Clamp
        lx = max(0, min(255, lx))
        ly = max(0, min(255, ly))
        rx = max(0, min(255, rx))
        ry = max(0, min(255, ry))

        return {
            "buttons": btn_mask,
            "dpad": dpad_val,
            "lx": lx,
            "ly": ly,
            "rx": rx,
            "ry": ry,
        }

    def to_bytes(self, state):
        """Pack Switch state into a compact binary packet for serial/network.

        Packet format (8 bytes):
          [0xAB] [buttons_hi] [buttons_lo] [dpad] [lx] [ly] [rx] [ry]
        """
        return struct.pack(
            "BBBBBBBB",
            0xAB,  # sync byte
            (state["buttons"] >> 8) & 0xFF,
            state["buttons"] & 0xFF,
            state["dpad"],
            state["lx"],
            state["ly"],
            state["rx"],
            state["ry"],
        )
