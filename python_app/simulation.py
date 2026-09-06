import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

import config
from ui.renderer_3d import draw_crane_scene
from ui.renderer_charts import render_panel_charts
from ui.widgets import Button
from ui.setpoint_panel import SetpointPanel
from ui.gl_utils import draw_grid

from models.crane_system import CraneSystem
from models.furuta_system import FurutaSystem
from models.quadrocopter_system import QuadrocopterSystem
from models.ball_and_plate_system import BallAndPlateSystem
from models.satellite_system import SatelliteSystem

from utils.data_logger import DataLogger  


def run_simulation(selected_mode, screen, clock, font_small, imu):
    gui_surface = pygame.Surface((config.PANEL_WIDTH, config.WINDOW_HEIGHT))

    # Initialize data logger instance
    logger = DataLogger()

    # Initialize and allocate GUI texture buffer
    gui_texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, gui_texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, config.PANEL_WIDTH, config.WINDOW_HEIGHT, 0, GL_RGB, GL_UNSIGNED_BYTE, None)

    # Initialize simulation model based on selected mode
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

    # --- INITIALIZE INDEPENDENT SETPOINT PANEL ---
    if selected_mode in ("BALL_AND_PLATE", "QUADROCOPTER"):
        setpoint_panel = SetpointPanel(num_inputs=2, labels=("SP X [m]", "SP Y [m]"), default_vals=("0.00", "0.00"), y=620)
    elif selected_mode in ("SATELLITE", "FURUTA"):
        setpoint_panel = SetpointPanel(num_inputs=1, labels=("SP Angle [deg]", ""), default_vals=("0.0", ""), y=620)
    else:  # CRANE
        setpoint_panel = SetpointPanel(num_inputs=1, labels=("SP Pos [m]", ""), default_vals=("0.00", ""), y=620)

    # Setpoint callback setup
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

    # --- DATA LOGGING BUTTON IN BOTTOM LEFT CORNER OF 3D VIEW ---
    btn_rec_y = config.WINDOW_HEIGHT - 45
    btn_record = Button(10, btn_rec_y, 200, 35, "START LOGGING")
    status_msg = ""
    status_msg_timer = 0.0

    last_ticks = pygame.time.get_ticks()

    try:
        while True:
            current_ticks = pygame.time.get_ticks()
            current_time_sec = current_ticks / 1000.0
            dt = (current_ticks - last_ticks) / 1000.0
            last_ticks = current_ticks
            if dt > 0.05:
                dt = 0.016

            # Sync setpoint input fields when not in MANUAL mode
            if setpoint_panel.current_mode != "MANUAL":
                if selected_mode in ("BALL_AND_PLATE", "QUADROCOPTER"):
                    setpoint_panel.update_text_fields(getattr(system, "setpoint_x", 0.0), getattr(system, "setpoint_y", 0.0))
                elif selected_mode == "SATELLITE":
                    setpoint_panel.update_text_fields(math.degrees(getattr(system, "setpoint_angle", 0.0)))
                elif selected_mode == "FURUTA":
                    setpoint_panel.update_text_fields(math.degrees(getattr(system, "target_angle", 0.0)))
                elif selected_mode == "CRANE":
                    setpoint_panel.update_text_fields(getattr(system, "setpoint_x", 0.0))

            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == QUIT:
                    return "QUIT"

                # Handle record button event (located in 3D viewport area)
                if btn_record.handle_event(event):
                    if not logger.is_recording:
                        logger.start_recording(current_time_sec)
                        btn_record.text = "STOP & SAVE (CSV)"
                        status_msg = "Recording started..."
                        status_msg_timer = current_time_sec + 2.0
                    else:
                        saved_path = logger.stop_and_save(selected_mode)
                        btn_record.text = "START LOGGING"
                        if saved_path:
                            status_msg = f"Saved to: {saved_path}"
                        else:
                            status_msg = "Save error / No data"
                        status_msg_timer = current_time_sec + 4.0
                    continue

                # Recalculate event coordinates for side panel
                event_panel = event
                if hasattr(event, "pos"):
                    event_dict = event.__dict__.copy()
                    event_dict["pos"] = (event.pos[0] - config.VIEW3D_WIDTH, event.pos[1])
                    event_panel = pygame.event.Event(event.type, event_dict)

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

                # Mouse interaction inside 3D viewport
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    if event.pos[0] < config.VIEW3D_WIDTH and setpoint_panel.current_mode == "MOUSE":
                        # Skip if record button was clicked
                        if not btn_record.rect.contains(pygame.Rect(event.pos, (1, 1))):
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
                                system.set_target_from_input(norm_x, my / config.WINDOW_HEIGHT)
                            else:
                                system.set_target_from_input(norm_x)

                # UI Controls inside side panel
                if hasattr(event, "pos") and event.pos[0] >= config.VIEW3D_WIDTH:
                    if hasattr(system, "get_widgets"):
                        for w in system.get_widgets():
                            if isinstance(w, Button) and w.handle_event(event_panel):
                                if hasattr(system, "reset_state"):
                                    system.reset_state()
                                elif hasattr(system, "reset"):
                                    system.reset()
                            else:
                                w.handle_event(event_panel)

            # IMU Hardware Data Processing
            if setpoint_panel.current_mode == "IMU" and imu is not None and imu.is_connected():
                raw_roll, raw_pitch = imu.get_orientation()
                if selected_mode in ("QUADROCOPTER", "BALL_AND_PLATE"):
                    if hasattr(system, "process_serial_data"):
                        system.process_serial_data(raw_roll, raw_pitch)
                elif selected_mode == "CRANE":
                    system.set_target_from_input(max(0.0, min(1.0, (raw_roll / 45.0 + 1.0) / 2.0)))
                elif selected_mode == "FURUTA":
                    if hasattr(system, "set_target_angle"):
                        system.set_target_angle(math.radians(raw_roll))
                elif selected_mode == "SATELLITE":
                    system.setpoint_angle = math.radians(raw_roll)

            # Step physics simulation
            if dt > 0:
                system.step(dt)

            # Sample telemetry data if recording is active
            logger.sample(current_time_sec, system)

            # --- RENDER 3D SCENE ---
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

            # --- RENDER 2D RECORD BUTTON OVERLAY ON 3D VIEWPORT ---
            glViewport(0, 0, config.VIEW3D_WIDTH, config.WINDOW_HEIGHT)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, config.VIEW3D_WIDTH, config.WINDOW_HEIGHT, 0, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)

            # Create surface overlay for 3D view
            overlay = pygame.Surface((config.VIEW3D_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
            btn_record.draw(overlay, font_small)

            if status_msg and current_time_sec < status_msg_timer:
                txt_color = (255, 80, 80) if logger.is_recording else (100, 255, 100)
                msg_surf = font_small.render(status_msg, True, txt_color)
                overlay.blit(msg_surf, (220, btn_rec_y + 10))

            tex_data = pygame.image.tostring(overlay, "RGBA", True)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDrawPixels(config.VIEW3D_WIDTH, config.WINDOW_HEIGHT, GL_RGBA, GL_UNSIGNED_BYTE, tex_data)
            glDisable(GL_BLEND)

            # --- RENDER SIDE GUI PANEL ---
            gui_surface.fill(config.COLOR_BG)

            titles = {
                "CRANE": "MODE: CRANE ANTI-SWAY (ESC: Return)",
                "BALL_AND_PLATE": "MODE: BALL & PLATE (ESC: Return)",
                "QUADROCOPTER": "MODE: QUADROCOPTER PID (ESC: Return)",
                "SATELLITE": "MODE: SATELLITE ORIENTATION (ESC: Return)",
                "FURUTA": "MODE: FURUTA PENDULUM (ESC: Return)",
            }
            title_txt = font_small.render(titles.get(selected_mode, ""), True, (0, 200, 255))
            gui_surface.blit(title_txt, (10, 10))

            if hasattr(system, "get_widgets"):
                for w in system.get_widgets():
                    w.draw(gui_surface, font_small)

            render_panel_charts(gui_surface, selected_mode, system, font_small)
            setpoint_panel.draw(gui_surface, font_small)

            # Update VRAM texture region for side panel
            texture_data = pygame.image.tostring(gui_surface, "RGB", True)
            glBindTexture(GL_TEXTURE_2D, gui_texture)
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, config.PANEL_WIDTH, config.WINDOW_HEIGHT, GL_RGB, GL_UNSIGNED_BYTE, texture_data)

            glViewport(config.VIEW3D_WIDTH, 0, config.PANEL_WIDTH, config.WINDOW_HEIGHT)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(0, config.PANEL_WIDTH, 0, config.WINDOW_HEIGHT, -1, 1)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
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