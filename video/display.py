"""
Low-latency display window using OpenCV.

Displays captured frames with minimal overhead. Supports fullscreen toggle
and FPS overlay.
"""

import time
import cv2


class Display:
    def __init__(self, title="Switch Cloud Play", fullscreen=False, show_fps=True):
        self.title = title
        self.fullscreen = fullscreen
        self.show_fps = show_fps
        self._frame_count = 0
        self._fps_time = time.time()
        self._fps = 0.0
        self._window_created = False

    def _create_window(self):
        if self._window_created:
            return
        cv2.namedWindow(self.title, cv2.WINDOW_NORMAL | cv2.WINDOW_GUI_NORMAL)
        if self.fullscreen:
            cv2.setWindowProperty(self.title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        self._window_created = True

    def show(self, frame, capture_time=None):
        """Display a frame. Returns True if the window should close.

        Args:
            frame: BGR numpy array from video source
            capture_time: time.time() taken right after frame was captured,
                          used to measure capture-to-display latency
        """
        self._create_window()

        # Calculate FPS
        self._frame_count += 1
        now = time.time()
        elapsed = now - self._fps_time
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._fps_time = now

        # Draw overlay
        if self.show_fps:
            label = f"{self._fps:.1f} FPS"
            if capture_time is not None:
                latency_ms = (now - capture_time) * 1000
                label += f" | {latency_ms:.0f}ms"
            cv2.putText(
                frame,
                label,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )

        cv2.imshow(self.title, frame)

        # Handle key events (1ms wait = minimal latency)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            return True
        elif key == ord("f") or key == 0x7A:  # F or F11-ish
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                cv2.setWindowProperty(self.title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(self.title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        return False

    def close(self):
        cv2.destroyAllWindows()
