import pygame
from ui.widgets import Button, TextInput


class CustomTextInput(TextInput):
    """Extension of TextInput featuring automatic content clearing upon click."""

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(self, "rect") and self.rect.collidepoint(event.pos):
                if not getattr(self, "active", False):
                    self.active = True
                    self.text = ""  # Clear text on click
                    return False
            else:
                self.active = False

        return super().handle_event(event)


class SetpointPanel:
    """
    Universal Setpoint panel for entering setpoint values and changing the control mode.
    """

    MODES = ["MANUAL", "IMU", "MOUSE"]

    def __init__(self, num_inputs=2, labels=("SP X [m]", "SP Y [m]"), default_vals=("0.00", "0.00"), x=20, y=590):
        self.num_inputs = num_inputs
        self.x = x
        self.y = y
        self.on_apply_callback = None
        self.on_mode_change_callback = None

        self.current_mode_idx = 0  # 0: MANUAL, 1: IMU, 2: MOUSE

        self.btn_height = 28
        self.btn_width = 130

        # Create mode button
        self.btn_mode = Button(x, y, self.btn_width, self.btn_height, self.current_mode)
        self.btn_send = Button(x + 140, y, 90, self.btn_height, "SEND")

        # Text input fields with proper vertical spacing
        row2_y = y + 52
        box_w = 100

        self.input1 = CustomTextInput(x, row2_y, box_w, self.btn_height, label=labels[0], default_text=default_vals[0])

        if self.num_inputs == 2:
            self.input2 = CustomTextInput(x + box_w + 10, row2_y, box_w, self.btn_height, label=labels[1], default_text=default_vals[1])
        else:
            self.input2 = None

    @property
    def current_mode(self):
        return self.MODES[self.current_mode_idx]

    def _update_button_label(self):
        """Rebuilds the button or updates its text depending on the Button class implementation."""
        if hasattr(self.btn_mode, "set_text"):
            self.btn_mode.set_text(self.current_mode)
        else:
            # If Button does not have set_text, replace the whole button object, forcing the updated label to render
            self.btn_mode = Button(self.x, self.y, self.btn_width, self.btn_height, self.current_mode)

    def set_callback(self, callback):
        self.on_apply_callback = callback

    def set_mode_change_callback(self, callback):
        self.on_mode_change_callback = callback

    def get_values(self):
        val1 = self.input1.get_value()
        if self.num_inputs == 1:
            return val1
        val2 = self.input2.get_value() if self.input2 else None
        return val1, val2

    def update_text_fields(self, val1, val2=None):
        if val1 is not None and not getattr(self.input1, "active", False):
            self.input1.text = f"{val1:.2f}"
        if self.num_inputs == 2 and val2 is not None and self.input2 is not None:
            if not getattr(self.input2, "active", False):
                self.input2.text = f"{val2:.2f}"

    def handle_event(self, event):
        # 1. Click on mode button (MODE)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(self.btn_mode, "rect") and self.btn_mode.rect.collidepoint(event.pos):
                self.current_mode_idx = (self.current_mode_idx + 1) % len(self.MODES)
                self._update_button_label()  # Force label update
                
                if self.on_mode_change_callback:
                    self.on_mode_change_callback(self.current_mode)
                return True

            if hasattr(self.btn_send, "rect") and self.btn_send.rect.collidepoint(event.pos):
                self.current_mode_idx = 0
                self._update_button_label()
                if self.on_mode_change_callback:
                    self.on_mode_change_callback(self.current_mode)
                if self.on_apply_callback:
                    self.on_apply_callback()
                return True

        # 2. Forward event to text input fields
        enter1 = self.input1.handle_event(event)
        enter2 = self.input2.handle_event(event) if self.num_inputs == 2 and self.input2 else False

        if enter1 or enter2:
            self.current_mode_idx = 0
            self._update_button_label()
            if self.on_mode_change_callback:
                self.on_mode_change_callback(self.current_mode)
            if self.on_apply_callback:
                self.on_apply_callback()
            return True

        return getattr(self.input1, "active", False) or (self.input2 and getattr(self.input2, "active", False))

    def draw(self, surface, font):
        self.btn_mode.draw(surface, font)
        self.btn_send.draw(surface, font)
        self.input1.draw(surface, font)
        if self.num_inputs == 2 and self.input2:
            self.input2.draw(surface, font)