import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import config
from ui.renderer_3d import draw_crane_scene
from ui.renderer_charts import render_panel_charts
from ui.widgets import Button, Slider
from ui.setpoint_panel import SetpointPanel
from ui.gl_utils import draw_grid

from models.crane_system import CraneSystem
from models.furuta_system import FurutaSystem
from models.quadrocopter_system import QuadrocopterSystem
from models.ball_and_plate_system import BallAndPlateSystem
from models.satellite_system import SatelliteSystem


def run_simulation(selected_mode, screen, clock, font_small, imu):
    gui_surface = pygame.Surface((config.PANEL_WIDTH, config.WINDOW_HEIGHT))

    # Inicjalizacja i alokacja bufora tekstury GUI
    gui_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, gui_texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, config.PANEL_WIDTH, config.WINDOW_HEIGHT, 0, GL_RGB, GL_UNSIGNED_BYTE, None)

    # Inicjalizacja modelu symulacji
    if selected_mode == "CRANE":
        system = CraneSystem(config)
    elif selected_mode == "FURUTA":
        system = FurutaSystem()
    elif selected_mode == "BALL_AND_PLATE":
        system = BallAndPlateSystem(config)
    elif selected_mode == "SATELLITE":
        system = SatelliteSystem(config)
    else:  # QUADROCOPTER
        system = QuadrocopterSystem(config)
        slider_kp = Slider(20, 45, 220, 12, 0.0, 20.0, system.pid_x.Kp, "Kp")
        slider_kd = Slider(20, 85, 220, 12, 0.0, 15.0, system.pid_x.Kd, "Kd")
        btn_reset = Button(20, 115, 220, 25, "RESET STANU (SPACE)")

    # --- INICJALIZACJA NIEZALEŻNEGO SETPOINT PANELU (Obniżona pozycja Y=620) ---
    if selected_mode in ("BALL_AND_PLATE", "QUADROCOPTER"):
        setpoint_panel = SetpointPanel(num_inputs=2, labels=("SP X [m]", "SP Y [m]"), default_vals=("0.00", "0.00"), y=620)
    elif selected_mode == "SATELLITE":
        setpoint_panel = SetpointPanel(num_inputs=1, labels=("SP Kąt [deg]", ""), default_vals=("0.0", ""), y=620)
    elif selected_mode == "FURUTA":
        setpoint_panel = SetpointPanel(num_inputs=1, labels=("SP Kąt [deg]", ""), default_vals=("0.0", ""), y=620)
    else:  # CRANE
        setpoint_panel = SetpointPanel(num_inputs=1, labels=("SP Pos [m]", ""), default_vals=("0.00", ""), y=620)

    # Callback po wciśnięciu WYŚLIJ / Enter
    def apply_setpoints():
        vals = setpoint_panel.get_values()
        if selected_mode in ("BALL_AND_PLATE", "QUADROCOPTER"):
            v1, v2 = vals
            if v1 is not None and hasattr(system, "setpoint_x"):
                system.setpoint_x = v1
            if v2 is not None and hasattr(system, "setpoint_y"):
                system.setpoint_y = v2
        elif selected_mode == "SATELLITE":
            if vals is not None and hasattr(system, "setpoint_angle"):
                system.setpoint_angle = math.radians(vals)
        elif selected_mode == "FURUTA":
            if vals is not None and hasattr(system, "set_target_angle"):
                system.set_target_angle(math.radians(vals))
        elif selected_mode == "CRANE":
            if vals is not None and hasattr(system, "setpoint_x"):
                system.setpoint_x = vals

    setpoint_panel.set_callback(apply_setpoints)

    # Bufory danych historycznych (QUADROCOPTER)
    hist_sp_x, hist_pv_x, hist_sp_y, hist_pv_y = [], [], [], []
    hist_roll, hist_pitch = [], []
    MAX_HIST = 150

    last_ticks = pygame.time.get_ticks()

    try:
        while True:
            current_ticks = pygame.time.get_ticks()
            dt = (current_ticks - last_ticks) / 1000.0
            last_ticks = current_ticks
            if dt > 0.05:
                dt = 0.016

            # Synchronizacja pól tekstowych, jeśli tryb to MOUSE/IMU
            if setpoint_panel.current_mode != "MANUAL":
                if selected_mode in ("BALL_AND_PLATE", "QUADROCOPTER"):
                    sp_x = getattr(system, "setpoint_x", 0.0)
                    sp_y = getattr(system, "setpoint_y", 0.0)
                    setpoint_panel.update_text_fields(sp_x, sp_y)
                elif selected_mode == "SATELLITE":
                    sp_angle = math.degrees(getattr(system, "setpoint_angle", 0.0))
                    setpoint_panel.update_text_fields(sp_angle)
                elif selected_mode == "FURUTA":
                    sp_angle = math.degrees(getattr(system, "target_angle", 0.0))
                    setpoint_panel.update_text_fields(sp_angle)
                elif selected_mode == "CRANE":
                    sp_x = getattr(system, "setpoint_x", 0.0)
                    setpoint_panel.update_text_fields(sp_x)

            # --- Obsługa zdarzeń ---
            for event in pygame.event.get():
                if event.type == QUIT:
                    return "QUIT"

                # Przygotowanie zdarzenia z przeliczoną pozycją dla panelu bocznego
                event_panel = event
                if hasattr(event, "pos"):
                    event_dict = event.__dict__.copy()
                    event_dict["pos"] = (event.pos[0] - config.VIEW3D_WIDTH, event.pos[1])
                    event_panel = pygame.event.Event(event.type, event_dict)

                # Przekazanie zdarzenia do SetpointPanel
                if setpoint_panel.handle_event(event_panel):
                    continue

                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        return "MENU"
                    elif event.key == K_SPACE:
                        if hasattr(system, "reset_state"):
                            system.reset_state()
                        elif hasattr(system, "reset"):
                            system.reset()

                # Kliknięcie na scenę 3D (ustawianie zadania myszą)
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    # Sterowanie kliknięciem na scenę działa TYLKO w trybie MOUSE
                    if event.pos[0] < config.VIEW3D_WIDTH and setpoint_panel.current_mode == "MOUSE":
                        mx, my = event.pos
                        norm_x = mx / config.VIEW3D_WIDTH
                        if selected_mode == "QUADROCOPTER":
                            system.setpoint_x = (norm_x - 0.5) * 2.4
                            system.setpoint_y = -(((my / config.WINDOW_HEIGHT) - 0.5) * 2.4)
                        elif selected_mode == "SATELLITE":
                            dx = mx - (config.VIEW3D_WIDTH / 2)
                            dy = (config.WINDOW_HEIGHT / 2) - my
                            system.setpoint_angle = math.atan2(dy, dx)
                        elif selected_mode in ("CRANE", "BALL_AND_PLATE"):
                            norm_y = my / config.WINDOW_HEIGHT
                            system.set_target_from_input(norm_x, norm_y)
                        else:
                            system.set_target_from_input(norm_x)

                # Zdarzenia pozostałych kontrolek UI
                if hasattr(event, "pos") and event.pos[0] >= config.VIEW3D_WIDTH:
                    if selected_mode == "QUADROCOPTER":
                        slider_kp.handle_event(event_panel)
                        slider_kd.handle_event(event_panel)
                        if btn_reset.handle_event(event_panel):
                            if hasattr(system, "setpoint_x"):
                                system.setpoint_x = system.setpoint_y = 0.0
                            if hasattr(system, "reset_state"):
                                system.reset_state()
                            elif hasattr(system, "reset"):
                                system.reset()
                    else:
                        if hasattr(system, "get_widgets"):
                            for w in system.get_widgets():
                                if isinstance(w, Button) and w.handle_event(event_panel):
                                    if hasattr(system, "reset_state"):
                                        system.reset_state()
                                    elif hasattr(system, "reset"):
                                        system.reset()
                                else:
                                    w.handle_event(event_panel)

            if selected_mode == "QUADROCOPTER":
                system.update_params(Kp=slider_kp.val, Kd=slider_kd.val)

            # Odczyt danych z IMU (tylko w trybie IMU)
            if setpoint_panel.current_mode == "IMU" and imu is not None and imu.is_connected():
                raw_roll, raw_pitch = imu.get_orientation()
                if selected_mode in ("QUADROCOPTER", "BALL_AND_PLATE"):
                    if hasattr(system, "process_serial_data"):
                        system.process_serial_data(raw_roll, raw_pitch)
                elif selected_mode == "CRANE":
                    norm_x = (raw_roll / 45.0 + 1.0) / 2.0
                    system.set_target_from_input(max(0.0, min(1.0, norm_x)))
                elif selected_mode == "FURUTA":
                    if hasattr(system, "set_target_angle"):
                        system.set_target_angle(math.radians(raw_roll))
                elif selected_mode == "SATELLITE":
                    system.setpoint_angle = math.radians(raw_roll)

            # Aktualizacja stanu fizycznego
            if dt > 0:
                if selected_mode == "QUADROCOPTER":
                    target_roll, target_pitch = system.step(dt)
                    ball_pos = getattr(system, "ball_pos", getattr(system, "pos", [0.0, 0.0]))
                    hist_sp_x.append(system.setpoint_x)
                    hist_pv_x.append(ball_pos[0])
                    hist_sp_y.append(system.setpoint_y)
                    hist_pv_y.append(ball_pos[1])
                    hist_roll.append(target_roll)
                    hist_pitch.append(target_pitch)

                    if len(hist_sp_x) > MAX_HIST:
                        hist_sp_x.pop(0); hist_pv_x.pop(0)
                        hist_sp_y.pop(0); hist_pv_y.pop(0)
                        hist_roll.pop(0); hist_pitch.pop(0)
                else:
                    system.step(dt)

            # --- Renderowanie Sceny 3D ---
            glClearColor(0.08, 0.09, 0.12, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            glViewport(0, 0, config.VIEW3D_WIDTH, config.WINDOW_HEIGHT)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(45, (config.VIEW3D_WIDTH / config.WINDOW_HEIGHT), 0.1, 50.0)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)
            glEnable(GL_LIGHT0)
            glEnable(GL_COLOR_MATERIAL)

            if selected_mode == "CRANE":
                glLightfv(GL_LIGHT0, GL_POSITION, [2.0, 4.0, 5.0, 1.0])
                gluLookAt(0.0, 0.2, 3.8, 0.0, 0.1, 0.0, 0.0, 1.0, 0.0)
                draw_crane_scene(system, system.setpoint_x)
            elif selected_mode == "FURUTA":
                glLightfv(GL_LIGHT0, GL_POSITION, [2.0, 4.0, 5.0, 1.0])
                gluLookAt(0.0, 0.25, 2.0, 0.0, 0.15, 0.0, 0.0, 1.0, 0.0)
                system.draw_3d()
            elif selected_mode == "BALL_AND_PLATE":
                glLightfv(GL_LIGHT0, GL_POSITION, [2.0, -4.0, 5.0, 1.0])
                glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.95, 1.0, 1.0])
                glLightfv(GL_LIGHT0, GL_AMBIENT, [0.25, 0.25, 0.3, 1.0])
                gluLookAt(0.0, -3.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
                draw_grid()
                (system.render_3d() if hasattr(system, "render_3d") else system.draw_3d())
            elif selected_mode == "SATELLITE":
                glLightfv(GL_LIGHT0, GL_POSITION, [2.0, 3.0, 5.0, 1.0])
                glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 0.95, 1.0])
                glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.28, 1.0])
                gluLookAt(0.0, 0.0, 4.2, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)
                system.render_3d()
            else:  # QUADROCOPTER
                glLightfv(GL_LIGHT0, GL_POSITION, [2.0, -4.0, 5.0, 1.0])
                glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.95, 1.0, 1.0])
                glLightfv(GL_LIGHT0, GL_AMBIENT, [0.25, 0.25, 0.3, 1.0])
                gluLookAt(0.0, -3.2, 2.6, 0.0, 0.0, 0.6, 0.0, 0.0, 1.0)
                draw_grid()
                (system.render_3d() if hasattr(system, "render_3d") else system.draw_3d())

            # --- Renderowanie Panelu Bocznego GUI ---
            gui_surface.fill(config.COLOR_BG)

            if selected_mode == "CRANE":
                title_txt = font_small.render("TRYB: CRANE ANTI-SWAY (ESC: Powrót)", True, (0, 200, 255))
                gui_surface.blit(title_txt, (10, 15))
                for w in system.get_widgets():
                    w.draw(gui_surface, font_small)

            elif selected_mode == "BALL_AND_PLATE":
                title_txt = font_small.render("TRYB: BALL & PLATE (ESC: Powrót)", True, (0, 200, 255))
                gui_surface.blit(title_txt, (10, 10))
                for w in system.get_widgets():
                    w.draw(gui_surface, font_small)

            elif selected_mode == "QUADROCOPTER":
                title_txt = font_small.render("TRYB: QUADROCOPTER PID (ESC: Powrót)", True, (0, 200, 255))
                gui_surface.blit(title_txt, (10, 10))
                slider_kp.draw(gui_surface, font_small)
                slider_kd.draw(gui_surface, font_small)
                btn_reset.draw(gui_surface, font_small)

            elif selected_mode == "SATELLITE":
                title_txt = font_small.render("TRYB: SATELLITE ORIENTATION (ESC: Powrót)", True, (0, 200, 255))
                gui_surface.blit(title_txt, (10, 10))
                for w in system.get_widgets():
                    w.draw(gui_surface, font_small)

            else:  # FURUTA
                title_txt = font_small.render("TRYB: FURUTA (ESC: Powrót)", True, (0, 200, 255))
                gui_surface.blit(title_txt, (10, 10))
                for w in system.get_widgets():
                    w.draw(gui_surface, font_small)

            # Rysowanie Wykresów
            extra_data = (hist_sp_x, hist_pv_x, hist_sp_y, hist_pv_y, hist_roll, hist_pitch) if selected_mode == "QUADROCOPTER" else None
            render_panel_charts(gui_surface, selected_mode, system, font_small, extra_hist_data=extra_data)

            # Rysowanie tekstu statusu
            if selected_mode != "QUADROCOPTER" and hasattr(system, "get_charts_data"):
                charts_data = system.get_charts_data()
                if "status_text" in charts_data and "status_color" in charts_data:
                    status_y = 550 if selected_mode == "BALL_AND_PLATE" else (480 if selected_mode == "FURUTA" else 490)
                    status_txt = font_small.render(charts_data["status_text"], True, charts_data["status_color"])
                    gui_surface.blit(status_txt, (15, status_y))

            # Rysowanie SetpointPanel
            setpoint_panel.draw(gui_surface, font_small)

            # Aktualizacja pod-obszaru tekstury VRAM
            texture_data = pygame.image.tostring(gui_surface, "RGB", True)
            glBindTexture(GL_TEXTURE_2D, gui_texture)
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, config.PANEL_WIDTH, config.WINDOW_HEIGHT, GL_RGB, GL_UNSIGNED_BYTE, texture_data)

            # Rysowanie kwadratu GUI w widoku Ortho
            glViewport(config.VIEW3D_WIDTH, 0, config.PANEL_WIDTH, config.WINDOW_HEIGHT)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, config.PANEL_WIDTH, 0, config.WINDOW_HEIGHT, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)
            glEnable(GL_TEXTURE_2D)

            glColor4f(1.0, 1.0, 1.0, 1.0)
            glBegin(GL_QUADS)
            glTexCoord2f(0, 0); glVertex2f(0, 0)
            glTexCoord2f(1, 0); glVertex2f(config.PANEL_WIDTH, 0)
            glTexCoord2f(1, 1); glVertex2f(config.PANEL_WIDTH, config.WINDOW_HEIGHT)
            glTexCoord2f(0, 1); glVertex2f(0, config.WINDOW_HEIGHT)
            glEnd()
            glDisable(GL_TEXTURE_2D)

            pygame.display.flip()
            clock.tick(config.FPS)

    finally:
        glDeleteTextures([gui_texture])