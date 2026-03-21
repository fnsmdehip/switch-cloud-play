"""
Read gamepad/controller input using pygame.

Supports any controller that macOS recognizes — Xbox, PS4/PS5, 8BitDo,
Pro Controller, etc. Outputs a normalized state dict.
"""

import pygame


class ControllerReader:
    def __init__(self, controller_index=0, deadzone=0.15):
        self.controller_index = controller_index
        self.deadzone = deadzone
        self.joystick = None
        self.name = None

        pygame.init()
        pygame.joystick.init()

        count = pygame.joystick.get_count()
        if count == 0:
            print("    [!] No controllers detected. Plug in a controller.")
            print("        Supported: Xbox, PS4/PS5, Pro Controller, 8BitDo, etc.")
            return

        self.joystick = pygame.joystick.Joystick(controller_index)
        self.joystick.init()
        self.name = self.joystick.get_name()
        print(f"    Controller: {self.name}")
        print(f"    Axes: {self.joystick.get_numaxes()}, "
              f"Buttons: {self.joystick.get_numbuttons()}, "
              f"Hats: {self.joystick.get_numhats()}")

    def _apply_deadzone(self, value):
        if abs(value) < self.deadzone:
            return 0.0
        return value

    def poll(self):
        """Poll controller state. Returns dict or None if no controller."""
        if not self.joystick:
            return None

        pygame.event.pump()

        axes = self.joystick.get_numaxes()
        buttons = self.joystick.get_numbuttons()
        hats = self.joystick.get_numhats()

        state = {
            # Analog sticks (normalized -1.0 to 1.0)
            "left_stick_x": self._apply_deadzone(self.joystick.get_axis(0) if axes > 0 else 0),
            "left_stick_y": self._apply_deadzone(self.joystick.get_axis(1) if axes > 1 else 0),
            "right_stick_x": self._apply_deadzone(self.joystick.get_axis(2) if axes > 2 else 0),
            "right_stick_y": self._apply_deadzone(self.joystick.get_axis(3) if axes > 3 else 0),
            # Triggers (0.0 to 1.0)
            "left_trigger": max(0, self.joystick.get_axis(4)) if axes > 4 else 0,
            "right_trigger": max(0, self.joystick.get_axis(5)) if axes > 5 else 0,
            # Buttons (bool)
            "buttons": [self.joystick.get_button(i) for i in range(buttons)],
            # D-pad (hat)
            "dpad": self.joystick.get_hat(0) if hats > 0 else (0, 0),
        }

        return state

    def close(self):
        if self.joystick:
            self.joystick.quit()
        pygame.joystick.quit()
