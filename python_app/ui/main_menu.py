import sys
import config
from OpenGL.GL import *
import pygame
from pygame.locals import *

# Pamiętaj o zaimportowaniu close_serial, jeśli używasz portu szeregowego
# from serial_utils import close_serial


class MainMenu:

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.options = [
            ("1. Suwnica", "Crane Anti-Sway Control"),
            ("2. Wahadło Furuty", "Inverted Pendulum LQR"),
            ("3. Quadrocopter", "PID + Median Filtering"),
            ("4. Ball and Plate", "2D Ball Balancing PID"),
            ("5. Satelita 3D", "Reaction Wheel Control"),
        ]

        self.mode_keys = [
            "CRANE",
            "FURUTA",
            "QUADROCOPTER",
            "BALL_AND_PLATE",
            "SATELLITE",
        ]
        self.hovered_index = -1

        pygame.font.init()
        self.font_title = pygame.font.SysFont("Segoe UI", 36, bold=True)
        self.font_subtitle = pygame.font.SysFont("Segoe UI", 16)
        self.font_card_title = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_card_desc = pygame.font.SysFont("Segoe UI", 13)

        self._recalculate_layout()

    def _recalculate_layout(self):
        card_w, card_h = 320, 140
        gap_x, gap_y = 30, 30

        row1_w = 3 * card_w + 2 * gap_x
        start_x_row1 = (self.width - row1_w) // 2
        start_y = 220

        row2_w = 2 * card_w + 1 * gap_x
        start_x_row2 = (self.width - row2_w) // 2

        self.cards = []
        for i, (title, desc) in enumerate(self.options):
            if i < 3:
                x = start_x_row1 + i * (card_w + gap_x)
                y = start_y
            else:
                x = start_x_row2 + (i - 3) * (card_w + gap_x)
                y = start_y + card_h + gap_y

            rect = pygame.Rect(x, y, card_w, card_h)
            self.cards.append(
                {"rect": rect, "title": title, "desc": desc, "id": i}
            )

    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            mx, my = event.pos
            old_hover = self.hovered_index
            self.hovered_index = -1
            for card in self.cards:
                if card["rect"].collidepoint(mx, my):
                    self.hovered_index = card["id"]
                    break
            # Zwraca True tylko wtedy, gdy stan najechania myszy się zmienił (potrzebne do przerysowania)
            return old_hover != self.hovered_index

        elif event.type == MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for card in self.cards:
                if card["rect"].collidepoint(mx, my):
                    return self.mode_keys[card["id"]]
        return False

    def draw(self, surface):
        surface.fill((15, 18, 26))

        title_txt = self.font_title.render(
            "CONTROL SYSTEMS LAB", True, (0, 210, 255)
        )
        sub_txt = self.font_subtitle.render(
            "Wybierz układ do symulacji i analizy regulatorów",
            True,
            (160, 175, 200),
        )

        surface.blit(
            title_txt, title_txt.get_rect(center=(self.width // 2, 85))
        )
        surface.blit(sub_txt, sub_txt.get_rect(center=(self.width // 2, 135)))

        pygame.draw.line(
            surface,
            (35, 45, 65),
            (self.width // 2 - 250, 165),
            (self.width // 2 + 250, 165),
            1,
        )

        for card in self.cards:
            rect = card["rect"]
            is_hovered = self.hovered_index == card["id"]

            bg_color = (28, 35, 52) if is_hovered else (20, 25, 38)
            border_color = (0, 190, 255) if is_hovered else (45, 55, 80)
            title_color = (255, 255, 255) if is_hovered else (210, 220, 240)
            desc_color = (140, 180, 220) if is_hovered else (110, 125, 150)

            pygame.draw.rect(surface, bg_color, rect, border_radius=12)
            pygame.draw.rect(
                surface,
                border_color,
                rect,
                width=2 if is_hovered else 1,
                border_radius=12,
            )

            t_surf = self.font_card_title.render(
                card["title"], True, title_color
            )
            d_surf = self.font_card_desc.render(card["desc"], True, desc_color)

            surface.blit(t_surf, (rect.x + 20, rect.y + 35))
            surface.blit(d_surf, (rect.x + 20, rect.y + 75))

            accent_color = (0, 210, 255) if is_hovered else (0, 120, 180)
            pygame.draw.rect(
                surface,
                accent_color,
                (rect.x + 8, rect.y + 30, 4, rect.h - 60),
                border_radius=2,
            )


def show_selection_menu(screen, clock):
    w, h = config.WINDOW_WIDTH, config.WINDOW_HEIGHT
    menu = MainMenu(w, h)

    # Inicjalizacja tekstury w OpenGL z odpowiednim rozmiarem
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, None
    )

    menu_surface = pygame.Surface((w, h))
    needs_update = True  # Flaga określająca konieczność odświeżenia tekstury GPU

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                glDeleteTextures([tex_id])
                # Jeśli zdefiniowałeś close_serial(), odkomentuj poniżej:
                # close_serial()
                pygame.quit()
                sys.exit()

            res = menu.handle_event(event)
            if isinstance(res, str):  # Został wybrany tryb
                glDeleteTextures([tex_id])
                return res
            elif res is True:  # Nastąpiła zmiana stanu hover
                needs_update = True

        # Aktualizacja tekstury na GPU tylko w przypadku zmiany stanu menu
        if needs_update:
            menu.draw(menu_surface)
            texture_data = pygame.image.tostring(menu_surface, "RGBA", True)

            glBindTexture(GL_TEXTURE_2D, tex_id)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
            # Użycie SubImage zapobiega alokacji nowej pamięci na karcie
            glTexSubImage2D(
                GL_TEXTURE_2D, 0, 0, 0, w, h, GL_RGBA, GL_UNSIGNED_BYTE, texture_data
            )
            needs_update = False

        # Rendering sceny 2D w OpenGL
        glClearColor(0.1, 0.12, 0.18, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, 0, h, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

        glBindTexture(GL_TEXTURE_2D, tex_id)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0)
        glVertex2f(0, 0)
        glTexCoord2f(1, 0)
        glVertex2f(w, 0)
        glTexCoord2f(1, 1)
        glVertex2f(w, h)
        glTexCoord2f(0, 1)
        glVertex2f(0, h)
        glEnd()

        glDisable(GL_TEXTURE_2D)

        pygame.display.flip()
        clock.tick(config.FPS)