#!/usr/bin/env python3
"""Quick test: verify capture card video works."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from video.capture_card import CaptureCardSource
from video.display import Display

source = CaptureCardSource(device_index=0)
display = Display(title="Capture Test", show_fps=True)

try:
    source.open()
except Exception as e:
    print(f"Failed: {e}")
    print("Plug in your capture card and try again.")
    sys.exit(1)

print("Showing capture card feed. Press ESC to quit.")
while True:
    frame = source.read()
    if frame is not None:
        if display.show(frame):
            break

source.close()
display.close()
