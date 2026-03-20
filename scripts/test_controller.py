#!/usr/bin/env python3
"""Quick test: verify controller input is being read."""

import sys
import time
sys.path.insert(0, "..")

from input.controller import ControllerReader

reader = ControllerReader(controller_index=0)

print("Reading controller input. Press Ctrl+C to quit.")
print("Move sticks and press buttons to see output.\n")

try:
    while True:
        state = reader.poll()
        if state:
            lx = state["left_stick_x"]
            ly = state["left_stick_y"]
            rx = state["right_stick_x"]
            ry = state["right_stick_y"]
            btns = [i for i, b in enumerate(state["buttons"]) if b]
            dpad = state["dpad"]
            print(
                f"\rL:({lx:+.2f},{ly:+.2f}) R:({rx:+.2f},{ry:+.2f}) "
                f"Btns:{btns} Dpad:{dpad}  ",
                end="", flush=True,
            )
        time.sleep(0.016)  # ~60Hz
except KeyboardInterrupt:
    pass

reader.close()
print("\nDone.")
