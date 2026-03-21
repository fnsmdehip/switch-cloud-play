"""
Capture video from an HDMI capture card via OpenCV.

The Switch dock outputs HDMI → capture card → USB to Mac.
Most USB3 HDMI capture cards ($10-30) work plug-and-play on macOS.
"""

import cv2


class CaptureCardSource:
    def __init__(self, device_index="auto", width=1920, height=1080, fps=60):
        self.device_index = device_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None

    def _find_capture_card(self):
        """Auto-detect capture card by skipping built-in cameras.

        Built-in Mac cameras (FaceTime) typically report 1280x720 or lower.
        Capture cards usually report 1920x1080 or have specific characteristics.
        """
        print("    Auto-detecting capture card...")
        candidates = []
        for i in range(10):
            cap = cv2.VideoCapture(i, cv2.CAP_AVFOUNDATION)
            if not cap.isOpened():
                continue
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            # Prefer devices that support 1080p+ (likely external capture cards)
            if w >= 1920:
                print(f"    Found capture card at device {i} ({w}x{h})")
                return i
            candidates.append((i, w, h))

        # No 1080p device found — pick the highest resolution non-zero device
        # (skip device 0 if there are others, since 0 is usually the webcam)
        if len(candidates) > 1:
            best = max(candidates[1:], key=lambda c: c[1] * c[2])
            print(f"    Best candidate: device {best[0]} ({best[1]}x{best[2]})")
            return best[0]
        elif candidates:
            print(f"    Only device found: {candidates[0][0]} ({candidates[0][1]}x{candidates[0][2]})")
            return candidates[0][0]

        raise RuntimeError(
            "No capture devices found. Plug in your HDMI capture card."
        )

    def open(self):
        if self.device_index == "auto":
            self.device_index = self._find_capture_card()

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
