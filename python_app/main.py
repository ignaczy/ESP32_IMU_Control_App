import math
from statistics import median
from collections import deque

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import config
import serial_handler
from renderers import draw_grid, draw_crane_scene
from ui.main_menu import show_selection_menu
from ui.charts import draw_chart
from ui.widgets import Button, Slider

from models.crane_system import CranePID, CraneSystem
from models.furuta_system import FurutaSystem
from models.quadrocopter_system import QuadrocopterSystem
from models.ball_and_plate_system import BallAndPlateSystem
from models.satellite_system import SatelliteSystem


def run_simulation(selected_mode, screen, clock, font_small, ser):
    gui_surface = pygame.Surface((config.PANEL_WIDTH, config.WINDOW_HEIGHT))

    gui_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, gui_texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    if selected_mode == "CRANE":
        system = CraneSystem()
        pid = CranePID(
            **getattr(
                config,
                "PID_CRANE_CONFIG",
                {"Kp_pos": 4.0, "Kd_pos": 2.0, "Kp_angle": 15.0, "Kd_angle": 3.0},
            )
        )
        slider_pos_kp = Slider(20, 50, 210, 12, 0.0, 20.0, pid.Kp_pos, "Kp Pozycja")
        slider_sway_kp = Slider(20, 100, 210, 12, 0.0, 50.0, pid.Kp_angle, "Kp Anti-Sway")
    elif selected_mode == "FURUTA":
        system = FurutaSystem()
    elif selected_mode == "BALL_AND_PLATE":
        system = BallAndPlateSystem(config)
        slider_kp = Slider(20, 45, 220, 12, 0.0, 15.0, system.pid_x.Kp, "Kp")
        slider_kd = Slider(20, 85, 220, 12, 0.0, 10.0, system.pid_x.Kd, "Kd")
        btn_reset = Button(20, 115, 220, 25, "RESET STANU (SPACE)")
    elif selected_mode == "SATELLITE":
        system = SatelliteSystem()
        slider_kp = Slider(20, 45, 220, 12, 0.0, 40.0, system.pid.Kp, "Kp")
        slider_kd = Slider(20, 85, 220, 12, 0.0, 30.0, system.pid.Kd, "Kd")
        btn_reset = Button(20, 115, 220, 25, "RESET STANU (SPACE)")
    else:  # QUADROCOPTER
        system = QuadrocopterSystem(config)
        slider_kp = Slider(20, 45, 220, 12, 0.0, 20.0, system.pid_x.Kp, "Kp")
        slider_kd = Slider(20, 85, 220, 12, 0.0, 15.0, system.pid_x.Kd, "Kd")
        btn_reset = Button(20, 115, 220, 25, "RESET STANU (SPACE)")

    setpoint_x = 0.0
    roll_buffer = deque([0.0] * 5, maxlen=5)

    hist_target_x, hist_cart_x, hist_sway_angle = [], [], []
    hist_sp_x, hist_pv_x, hist_sp_y, hist_pv_y = [], [], [], []
    hist_roll, hist_pitch, hist_wheel_speed = [], [], []
    MAX_HIST = 150

    last_ticks = pygame.time.get_ticks()

    while True:
        current_ticks = pygame.time.get_ticks()
        dt = (current_ticks - last_ticks) / 1000.0
        last_ticks = current_ticks
        if dt > 0.05:
            dt = 0.016

        for event in pygame.event.get():
            if event.type == QUIT:
                glDeleteTextures([gui_texture])
                return "QUIT"

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    glDeleteTextures([gui_texture])
                    return "MENU"
                elif event.key == K_SPACE:
                    setpoint_x = 0.0
                    (
                        system.reset_state()
                        if hasattr(system, "reset_state")
                        else system.reset()
                    )

            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                if event.pos[0] < config.VIEW3D_WIDTH:
                    mx, my = event.pos
                    norm_x = mx / config.VIEW3D_WIDTH
                    if selected_mode == "CRANE":
                        setpoint_x = (norm_x - 0.5) * 4.0
                    elif selected_mode in ("QUADROCOPTER", "BALL_AND_PLATE"):
                        system.setpoint_x = ((mx / config.VIEW3D_WIDTH) - 0.5) * 2.4
                        system.setpoint_y = -(((my / config.WINDOW_HEIGHT) - 0.5) * 2.4)
                    elif selected_mode == "SATELLITE":
                        dx = mx - (config.VIEW3D_WIDTH / 2)
                        dy = (config.WINDOW_HEIGHT / 2) - my
                        system.setpoint_angle = math.atan2(dy, dx)
                    else:
                        system.set_target_from_input(norm_x)

            if event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION):
                if event.pos[0] >= config.VIEW3D_WIDTH:
                    event_panel = pygame.event.Event(event.type, event.__dict__)
                    event_panel.pos = (event.pos[0] - config.VIEW3D_WIDTH, event.pos[1])

                    if selected_mode == "CRANE":
                        slider_pos_kp.handle_event(event_panel)
                        slider_sway_kp.handle_event(event_panel)
                    elif selected_mode in ("QUADROCOPTER", "BALL_AND_PLATE", "SATELLITE"):
                        slider_kp.handle_event(event_panel)
                        slider_kd.handle_event(event_panel)
                        if btn_reset.handle_event(event_panel):
                            if hasattr(system, "setpoint_x"):
                                system.setpoint_x = system.setpoint_y = 0.0
                            if hasattr(system, "setpoint_angle"):
                                system.setpoint_angle = 0.0
                            system.reset_state()
                    else:
                        for w in system.get_widgets():
                            w.handle_event(event_panel)

        if selected_mode == "CRANE":
            pid.Kp_pos = slider_pos_kp.val
            pid.Kp_angle = slider_sway_kp.val
        elif selected_mode in ("QUADROCOPTER", "BALL_AND_PLATE"):
            system.update_params(Kp=slider_kp.val, Kd=slider_kd.val)
        elif selected_mode == "SATELLITE":
            system.pid.Kp = slider_kp.val
            system.pid.Kd = slider_kd.val

        if ser is not None and ser.in_waiting:
            try:
                raw_data = ser.read_all().decode("utf-8", errors="ignore").splitlines()
                if raw_data:
                    latest_line = raw_data[-1]
                    if "ROLL:" in latest_line:
                        parts = latest_line.split(",")
                        raw_roll = float(parts[0].split(":")[1])

                        if selected_mode in ("QUADROCOPTER", "BALL_AND_PLATE") and "PITCH:" in latest_line:
                            raw_pitch = float(parts[1].split(":")[1])
                            system.process_serial_data(raw_roll, raw_pitch)
                        else:
                            if abs(raw_roll) > 0.0001:
                                roll_buffer.append(raw_roll)
                            filtered_roll = median(roll_buffer)

                            if selected_mode == "CRANE":
                                setpoint_x = max(-1.8, min(1.8, (filtered_roll / 45.0) * 1.8))
                            elif selected_mode == "FURUTA":
                                system.set_target_angle(math.radians(filtered_roll))
                            elif selected_mode == "SATELLITE":
                                system.setpoint_angle = math.radians(filtered_roll)
            except Exception:
                pass

        if dt > 0:
            if selected_mode == "CRANE":
                force = pid.update(setpoint_x, system.x, system.vx, system.theta, system.omega, dt)
                system.step(force, dt)

                hist_target_x.append(setpoint_x)
                hist_cart_x.append(system.x)
                hist_sway_angle.append(math.degrees(system.theta))
                if len(hist_target_x) > MAX_HIST:
                    hist_target_x.pop(0)
                    hist_cart_x.pop(0)
                    hist_sway_angle.pop(0)
            elif selected_mode in ("QUADROCOPTER", "BALL_AND_PLATE"):
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
            elif selected_mode == "SATELLITE":
                system.update(dt)
                hist_sp_x.append(math.degrees(system.setpoint_angle))
                hist_pv_x.append(math.degrees(system.angle_sat))
                hist_wheel_speed.append(system.omega_wheel)

                if len(hist_sp_x) > MAX_HIST:
                    hist_sp_x.pop(0); hist_pv_x.pop(0); hist_wheel_speed.pop(0)
            else:
                system.step(dt)

        # Rysowanie Sceny 3D
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
            draw_crane_scene(system, setpoint_x)
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
            system.render_3d()

        # Rysowanie Panelu Bocznego
        gui_surface.fill(config.COLOR_BG)

        if selected_mode == "CRANE":
            title_txt = font_small.render("TRYB: CRANE ANTI-SWAY (ESC: Powrót)", True, (0, 200, 255))
            gui_surface.blit(title_txt, (10, 15))

            slider_pos_kp.draw(gui_surface, font_small)
            slider_sway_kp.draw(gui_surface, font_small)

            draw_chart(
                gui_surface,
                pygame.Rect(10, 160, config.PANEL_WIDTH - 20, 150),
                font_small,
                "Pozycja Wozka X [m]",
                -2.0,
                2.0,
                [
                    {"data": hist_target_x, "color": (50, 220, 130)},
                    {"data": hist_cart_x, "color": (80, 170, 255)},
                ],
            )
            draw_chart(
                gui_surface,
                pygame.Rect(10, 330, config.PANEL_WIDTH - 20, 150),
                font_small,
                "Kat Kolysania [deg]",
                -30.0,
                30.0,
                [{"data": hist_sway_angle, "color": (255, 90, 90)}],
            )
        elif selected_mode in ("QUADROCOPTER", "BALL_AND_PLATE"):
            mode_name = "BALL & PLATE PID" if selected_mode == "BALL_AND_PLATE" else "QUADROCOPTER PID"
            title_txt = font_small.render(f"TRYB: {mode_name} (ESC: Powrót)", True, (0, 200, 255))
            gui_surface.blit(title_txt, (10, 10))

            slider_kp.draw(gui_surface, font_small)
            slider_kd.draw(gui_surface, font_small)
            btn_reset.draw(gui_surface, font_small)

            draw_chart(
                gui_surface,
                pygame.Rect(10, 150, config.PANEL_WIDTH - 20, 130),
                font_small,
                "Pozycja X [m]",
                -1.5,
                1.5,
                [
                    {"data": hist_sp_x, "color": (80, 220, 120)},
                    {"data": hist_pv_x, "color": (100, 200, 255)},
                ],
            )
            draw_chart(
                gui_surface,
                pygame.Rect(10, 290, config.PANEL_WIDTH - 20, 130),
                font_small,
                "Pozycja Y [m]",
                -1.5,
                1.5,
                [
                    {"data": hist_sp_y, "color": (80, 220, 120)},
                    {"data": hist_pv_y, "color": (200, 100, 255)},
                ],
            )
            chart_angle_title = "Katy Plytki [deg]" if selected_mode == "BALL_AND_PLATE" else "Zadane Katy [deg]"
            draw_chart(
                gui_surface,
                pygame.Rect(10, 430, config.PANEL_WIDTH - 20, 130),
                font_small,
                chart_angle_title,
                -20.0,
                20.0,
                [
                    {"data": hist_roll, "color": (255, 90, 90)},
                    {"data": hist_pitch, "color": (180, 130, 255)},
                ],
            )
        elif selected_mode == "SATELLITE":
            title_txt = font_small.render("TRYB: SATELLITE ORIENTATION (ESC: Powrót)", True, (0, 200, 255))
            gui_surface.blit(title_txt, (10, 10))

            slider_kp.draw(gui_surface, font_small)
            slider_kd.draw(gui_surface, font_small)
            btn_reset.draw(gui_surface, font_small)

            draw_chart(
                gui_surface,
                pygame.Rect(10, 150, config.PANEL_WIDTH - 20, 150),
                font_small,
                "Orientacja Satelity [deg]",
                -180.0,
                180.0,
                [
                    {"data": hist_sp_x, "color": (80, 220, 120)},
                    {"data": hist_pv_x, "color": (255, 180, 50)},
                ],
            )
            draw_chart(
                gui_surface,
                pygame.Rect(10, 330, config.PANEL_WIDTH - 20, 150),
                font_small,
                "Predkosc Kola Zamachowego [rad/s]",
                -300.0,
                300.0,
                [{"data": hist_wheel_speed, "color": (100, 200, 255)}],
            )
        else:
            title_txt = font_small.render("TRYB: FURUTA (ESC: Powrót)", True, (0, 200, 255))
            gui_surface.blit(title_txt, (10, 10))

            for w in system.get_widgets():
                w.draw(gui_surface, font_small)

            charts_data = system.get_charts_data()
            draw_chart(
                gui_surface,
                pygame.Rect(10, 210, config.PANEL_WIDTH - 20, 120),
                font_small,
                "Kat Wahadla [deg]",
                -180.0,
                180.0,
                charts_data["pendulum_chart"],
            )
            draw_chart(
                gui_surface,
                pygame.Rect(10, 345, config.PANEL_WIDTH - 20, 120),
                font_small,
                "Kat Ramienia i Zadany [deg]",
                -180.0,
                180.0,
                charts_data["arm_chart"],
            )
            status_txt = font_small.render(
                charts_data["status_text"], True, charts_data["status_color"]
            )
            gui_surface.blit(status_txt, (15, 480))

        texture_data = pygame.image.tostring(gui_surface, "RGB", True)

        glViewport(config.VIEW3D_WIDTH, 0, config.PANEL_WIDTH, config.WINDOW_HEIGHT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, config.PANEL_WIDTH, 0, config.WINDOW_HEIGHT, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

        glBindTexture(GL_TEXTURE_2D, gui_texture)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, config.PANEL_WIDTH, config.WINDOW_HEIGHT, 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)

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


def main():
    pygame.init()
    screen = pygame.display.set_mode(
        (config.WINDOW_WIDTH, config.WINDOW_HEIGHT), DOUBLEBUF | OPENGL
    )
    pygame.display.set_caption("Control Systems Lab")

    clock = pygame.time.Clock()
    font_small = pygame.font.SysFont("Segoe UI", 12)

    ser = serial_handler.init_serial()

    while True:
        selected_mode = show_selection_menu(screen, clock)
        result = run_simulation(selected_mode, screen, clock, font_small, ser)

        if result == "QUIT":
            break

    serial_handler.close_serial()
    pygame.quit()


if __name__ == "__main__":
    main()