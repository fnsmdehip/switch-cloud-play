"""
Capture video from an HDMI capture card via OpenCV.

The Switch dock outputs HDMI → capture card → USB to Mac.
Most USB3 HDMI capture cards ($10-30) work plug-and-play on macOS.
"""

import cv2


class CaptureCardSource:
    def __init__(self, device_index=0, width=1920, height=1080, fps=60):
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None

    def open(self):
        # Use AVFoundation backend on macOS for lowest latency
        self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_AVFOUNDATION)
        if not self.cap.isOpened():
            # Fallback to default backend
            self.cap = cv2.VideoCapture(self.device_index)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Cannot open capture device {self.device_index}. "
                "Check that your capture card is connected."
            )

        # Set capture properties for low latency
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        # Minimize buffer to reduce latency (only buffer 1 frame)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # Use MJPEG if available (lower latency than raw)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))

        actual_w = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"    Capture card opened: {int(actual_w)}x{int(actual_h)} @ {actual_fps:.0f}fps")

    def read(self):
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    @staticmethod
    def list_devices():
        """Try to enumerate available video capture devices."""
        print("Scanning for video capture devices...")
        found = []
        for i in range(10):
            cap = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                print(f"  Device {i}: {w}x{h}")
                found.append(i)
                cap.release()
        if not found:
            print("  No devices found. Make sure your capture card is connected.")
        return found
