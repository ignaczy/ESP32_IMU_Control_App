import pygame
import config
from ui.charts import draw_chart
import math

def render_panel_charts(gui_surface, selected_mode, system, font_small, extra_hist_data=None):
    """
    Renders the charts and prints a single status text line directly below the chart bounding box.
    """
    chart_rect = None
    status_text = ""
    status_color = (0, 255, 100)

    if selected_mode == "CRANE":
        charts_data = system.get_charts_data()
        
        charts = [
            {"title": "Trolley Position X [m]", "min_val": -2.0, "max_val": 2.0, "series": charts_data.get("pos_chart", [])},
            {"title": "Sway Angle [deg]", "min_val": -30.0, "max_val": 30.0, "series": charts_data.get("sway_chart", [])},
            {"title": "Control Signal F [N]", "min_val": -system.pid.max_force, "max_val": system.pid.max_force, "series": charts_data.get("u_chart", [])}
        ]
        
        chart_rect = pygame.Rect(10, 270, config.PANEL_WIDTH - 20, 310)
        status_text = getattr(system, "status_text", "")
        status_color = getattr(system, "status_color", (0, 255, 100))
        draw_chart(gui_surface, chart_rect, font_small, charts)

    elif selected_mode == "BALL_AND_PLATE":
        charts_data = system.get_charts_data()
        
        charts = [
            {"title": "Position X [m]", "min_val": -1.5, "max_val": 1.5, "series": charts_data.get("pos_x_chart", [])},
            {"title": "Position Y [m]", "min_val": -1.5, "max_val": 1.5, "series": charts_data.get("pos_y_chart", [])},
            {"title": "Control Signal U [deg]", "min_val": -20.0, "max_val": 20.0, "series": charts_data.get("u_chart", [])}
        ]
        
        chart_rect = pygame.Rect(10, 180, config.PANEL_WIDTH - 20, 350)

        status_text = getattr(system, "status_text", "")
        status_color = getattr(system, "status_color", (0, 255, 100))
        draw_chart(gui_surface, chart_rect, font_small, charts)

    elif selected_mode == "QUADROCOPTER":
        charts_data = system.get_charts_data()
        limit = getattr(system, "pid_limit", 15.0)

        charts = [
            {"title": "Position X [m]", "min_val": -2.0, "max_val": 2.0, "series": charts_data.get("pos_x_chart", [])},
            {"title": "Position Y [m]", "min_val": -2.0, "max_val": 2.0, "series": charts_data.get("pos_y_chart", [])},
            {"title": "Control Signal U [deg]", "min_val": -limit, "max_val": limit, "series": charts_data.get("u_chart", [])}
        ]
        
        chart_rect = pygame.Rect(10, 180, config.PANEL_WIDTH - 20, 350)

        status_text = getattr(system, "status_text", "")
        status_color = getattr(system, "status_color", (0, 255, 100))
        draw_chart(gui_surface, chart_rect, font_small, charts)

    elif selected_mode == "SATELLITE":
        charts_data = system.get_charts_data()
        charts = [
            {"title": "Satellite Orientation [deg]", "min_val": -180.0, "max_val": 180.0, "series": charts_data.get("satellite_chart", [])},
            {"title": "Flywheel Velocity [rad/s]", "min_val": -system.max_wheel_speed, "max_val": system.max_wheel_speed, "series": charts_data.get("wheel_chart", [])},
        ]
        if "u_chart" in charts_data:
            charts.append({"title": "Control Torque M [Nm]", "min_val": -25.0, "max_val": 25.0, "series": charts_data["u_chart"]})
            chart_rect = pygame.Rect(10, 175, config.PANEL_WIDTH - 20, 370)
        else:
            chart_rect = pygame.Rect(10, 175, config.PANEL_WIDTH - 20, 320)

        status_text = getattr(system, "status_text", "")
        status_color = getattr(system, "status_color", (0, 255, 100))
        draw_chart(gui_surface, chart_rect, font_small, charts)

    elif selected_mode == "FURUTA":
        charts_data = system.get_charts_data()
        max_torque = getattr(system.controller, "max_torque", 5.0)

        charts = [
            {"title": "Pendulum Angle [deg]", "min_val": -180.0, "max_val": 180.0, "series": charts_data.get("pendulum_chart", [])},
            {"title": "Arm & Setpoint Angle [deg]", "min_val": -180.0, "max_val": 180.0, "series": charts_data.get("arm_chart", [])},
            {"title": "Control Torque M [Nm]", "min_val": -max_torque, "max_val": max_torque, "series": charts_data.get("u_chart", [])}
        ]
        
        chart_rect = pygame.Rect(10, 210, config.PANEL_WIDTH - 20, 330)
        status_text = getattr(system, "status_text", "")
        status_color = getattr(system, "status_color", (0, 255, 100))
        draw_chart(gui_surface, chart_rect, font_small, charts)

    # DRAW STATUS EXACTLY ONCE BELOW THE CHART BOUNDING BOX
    if chart_rect and status_text:
        txt_surf = font_small.render(status_text, True, status_color)
        gui_surface.blit(txt_surf, (10, chart_rect.bottom + 10))