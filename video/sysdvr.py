"""
Receive video from SysDVR (Nintendo Switch homebrew).

SysDVR streams 720p@30fps h264 video from Switch over USB or TCP.
This module connects to the SysDVR TCP stream and decodes frames.

Requires: SysDVR installed on Switch (needs CFW/Atmosphere).
GitHub: https://github.com/exelix11/SysDVR
"""

import subprocess
import cv2
import numpy as np


class SysDVRSource:
    def __init__(self, mode="tcp", switch_ip=None, port=6666):
        self.mode = mode
        self.switch_ip = switch_ip
        self.port = port
        self.cap = None

    def open(self):
        if self.mode == "tcp":
            if not self.switch_ip:
                raise ValueError("switch_ip required for TCP mode. Set in config.yaml")
            # SysDVR TCP bridge exposes an RTSP-like stream
            # The default SysDVR client uses a custom protocol, but we can use
            # the built-in RTSP mode or pipe through ffmpeg
            stream_url = f"tcp://{self.switch_ip}:{self.port}"
            print(f"    Connecting to SysDVR at {stream_url}")

            # Use ffmpeg to decode the SysDVR stream and pipe raw frames
            # SysDVR's TCP mode sends raw h264 NALUs
            ffmpeg_cmd = [
                "ffmpeg",
                "-i", stream_url,
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "-vf", "scale=1280:720",
                # Low latency flags
                "-fflags", "nobuffer",
                "-flags", "low_delay",
                "-probesize", "32",
                "-analyzeduration", "0",
                "-tune", "zerolatency",
                "-"
            ]
            self._ffmpeg = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            self._frame_size = 1280 * 720 * 3
        elif self.mode == "usb":
            # For USB mode, SysDVR exposes a virtual video device
            # Try to find it via OpenCV
            print("    Looking for SysDVR USB device...")
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    if w == 1280 and h == 720:
                        self.cap = cap
                        print(f"    Found SysDVR USB at device {i}")
                        return
                    cap.release()
            raise RuntimeError("SysDVR USB device not found")
        else:
            raise ValueError(f"Unknown SysDVR mode: {self.mode}")

    def read(self):
        if self.mode == "tcp":
            raw = self._ffmpeg.stdout.read(self._frame_size)
            if len(raw) != self._frame_size:
                return None
            frame = np.frombuffer(raw, dtype=np.uint8).reshape((720, 1280, 3))
            return frame
        elif self.mode == "usb" and self.cap:
            ret, frame = self.cap.read()
            return frame if ret else None
        return None

    def close(self):
        if self.mode == "tcp" and hasattr(self, "_ffmpeg"):
            self._ffmpeg.terminate()
            self._ffmpeg.wait()
        if self.cap:
            self.cap.release()
