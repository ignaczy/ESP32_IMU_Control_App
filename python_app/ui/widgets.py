import pygame
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
import config

class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label, step=0.1):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.label = label
        self.dragging = False
        self.val = self._snap(initial_val)

    def _snap(self, val):
        """Rounds the slider value to the specified step."""
        snapped = round((val - self.min_val) / self.step) * self.step + self.min_val
        return max(self.min_val, min(self.max_val, snapped))

    def draw(self, surface, font):
        # Slider background
        pygame.draw.rect(surface, (45, 52, 70), self.rect, border_radius=4)
        
        # Slider handle
        norm_pos = (self.val - self.min_val) / (self.max_val - self.min_val) if self.max_val != self.min_val else 0
        handle_x = self.rect.x + int(norm_pos * self.rect.w)
        handle_rect = pygame.Rect(handle_x - 6, self.rect.y - 3, 12, self.rect.h + 6)
        pygame.draw.rect(surface, config.COLOR_SLIDER_HANDLE, handle_rect, border_radius=4)

        # Label with value
        txt = font.render(f"{self.label}: {self.val:.2f}", True, config.COLOR_TEXT)
        surface.blit(txt, (self.rect.x, self.rect.y - 16))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._update_val(event.pos[0])
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == MOUSEMOTION and self.dragging:
            self._update_val(event.pos[0])

    def _update_val(self, mouse_x):
        rel_x = max(0, min(mouse_x - self.rect.x, self.rect.w))
        raw_val = self.min_val + (rel_x / self.rect.w) * (self.max_val - self.min_val)
        self.val = self._snap(raw_val)


class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.is_hovered = False

    def draw(self, surface, font):
        color = config.COLOR_BTN_RESET_HOVER if self.is_hovered else config.COLOR_BTN_RESET
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=1, border_radius=6)

        txt = font.render(self.label, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=self.rect.center)
        surface.blit(txt, txt_rect)

    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


def draw_chart(surface, rect, font, title, y_min, y_max, data_series):
    """Draws a real-time line chart for the given data series."""
    pygame.draw.rect(surface, config.COLOR_PANEL_BG, rect, border_radius=6)
    pygame.draw.rect(surface, config.COLOR_PANEL_BORDER, rect, width=1, border_radius=6)

    title_txt = font.render(title, True, config.COLOR_TEXT)
    surface.blit(title_txt, (rect.x + 8, rect.y + 4))

    ax_x = rect.x + 38
    ax_y = rect.y + 22
    ax_w = rect.w - 48
    ax_h = rect.h - 30

    # Grid lines
    for i in range(3):
        gy = ax_y + ax_h * (i / 2.0)
        val = y_max - (i / 2.0) * (y_max - y_min)
        pygame.draw.line(surface, (50, 58, 78), (ax_x, gy), (ax_x + ax_w, gy), 1)
        lbl = font.render(f"{val:>4.1f}", True, (160, 172, 195))
        surface.blit(lbl, (rect.x + 2, gy - 6))

    pygame.draw.rect(surface, (90, 102, 130), (ax_x, ax_y, ax_w, ax_h), 1)

    # Drawing data series
    for series in data_series:
        data = series["data"]
        color = series["color"]
        if len(data) > 1:
            pts = []
            max_samples = len(data)
            for i, val in enumerate(data):
                px = ax_x + i * (ax_w / (max_samples - 1 if max_samples > 1 else 1))
                clamped_val = max(y_min, min(y_max, val))
                norm_val = (clamped_val - y_min) / (y_max - y_min)
                py = ax_y + ax_h * (1.0 - norm_val)
                pts.append((px, py))
            pygame.draw.aalines(surface, color, False, pts)

class TextInput:
    """Simple text field widget for value input."""
    def __init__(self, x, y, width, height, label="", default_text="0.00"):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = str(default_text)
        self.label = label
        self.active = False
        self.color_inactive = (70, 70, 80)
        self.color_active = (0, 200, 255)
        self.bg_color = (20, 20, 30)
        self.text_color = (255, 255, 255)

    def handle_event(self, event):
        """Handles mouse clicks and keyboard typing. Returns True when Enter is pressed."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Activate the field if clicked inside its area
            self.active = self.rect.collidepoint(event.pos)
            return False

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self.active = False
                return True  # ENTER pressed (confirmation)
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # Accept only digits, period, and minus sign
                if event.unicode in "0123456789.-":
                    self.text += event.unicode
        return False

    def get_value(self):
        """Returns the parsed float value or None if the entered text is invalid."""
        try:
            return float(self.text)
        except ValueError:
            return None

    def draw(self, surface, font):
        # Label above the field with a smaller size or offset
        if self.label:
            label_surf = font.render(self.label, True, (160, 160, 170))
            surface.blit(label_surf, (self.rect.x, self.rect.y - 14))

        color = self.color_active if self.active else self.color_inactive
        pygame.draw.rect(surface, self.bg_color, self.rect)
        pygame.draw.rect(surface, color, self.rect, 1)

        txt_surf = font.render(self.text, True, self.text_color)
        surface.blit(txt_surf, (self.rect.x + 4, self.rect.y + 2))