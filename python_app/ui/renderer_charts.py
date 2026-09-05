import pygame
import config
from ui.charts import draw_chart
import math

def render_panel_charts(gui_surface, selected_mode, system, font_small, extra_hist_data=None):
    """
    Rysuje wykresy oraz wypisuje pojedynczy tekst statusu dokładnie pod ramką wykresu.
    """
    chart_rect = None
    status_text = ""
    status_color = (0, 255, 100)

    if selected_mode == "CRANE":
        charts_data = system.get_charts_data()
        
        charts = [
            {"title": "Pozycja Wozka X [m]", "min_val": -2.0, "max_val": 2.0, "series": charts_data.get("pos_chart", [])},
            {"title": "Kat Kolysania [deg]", "min_val": -30.0, "max_val": 30.0, "series": charts_data.get("sway_chart", [])},
            {"title": "Sygnal Sterujacy F [N]", "min_val": -system.pid.max_force, "max_val": system.pid.max_force, "series": charts_data.get("u_chart", [])}
        ]
        
        chart_rect = pygame.Rect(10, 270, config.PANEL_WIDTH - 20, 310)
        status_text = getattr(system, "status_text", "")
        status_color = getattr(system, "status_color", (0, 255, 100))
        draw_chart(gui_surface, chart_rect, font_small, charts)

    elif selected_mode == "BALL_AND_PLATE":
        charts_data = system.get_charts_data()
        
        # Zawsze uwzględniamy 4 wykresy (w tym sygnał sterujący U)
        charts = [
            {"title": "Pozycja X [m]", "min_val": -1.5, "max_val": 1.5, "series": charts_data.get("pos_x_chart", [])},
            {"title": "Pozycja Y [m]", "min_val": -1.5, "max_val": 1.5, "series": charts_data.get("pos_y_chart", [])},
            {"title": "Katy Plytki [deg]", "min_val": -20.0, "max_val": 20.0, "series": charts_data.get("angles_chart", [])},
            {"title": "Sygnal Sterujacy U [deg]", "min_val": -20.0, "max_val": 20.0, "series": charts_data.get("u_chart", [])}
        ]
        
        # Dostosowana wysokość prostokąta, aby 4 wykresy mieściły się poprawnie
        chart_rect = pygame.Rect(10, 150, config.PANEL_WIDTH - 20, 440)

        status_text = getattr(system, "status_text", "")
        status_color = getattr(system, "status_color", (0, 255, 100))
        draw_chart(gui_surface, chart_rect, font_small, charts)

    elif selected_mode == "QUADROCOPTER":
        charts_data = system.get_charts_data()
        limit = getattr(system, "pid_limit", 15.0)

        charts = [
            {"title": "Pozycja X [m]", "min_val": -2.0, "max_val": 2.0, "series": charts_data.get("pos_x_chart", [])},
            {"title": "Pozycja Y [m]", "min_val": -2.0, "max_val": 2.0, "series": charts_data.get("pos_y_chart", [])},
            {"title": "Katy Rzeczywiste [deg]", "min_val": -20.0, "max_val": 20.0, "series": charts_data.get("angles_chart", [])},
        ]
        if "u_chart" in charts_data:
            charts.append({"title": "Sygnal Sterujacy U [deg]", "min_val": -limit, "max_val": limit, "series": charts_data["u_chart"]})
            chart_rect = pygame.Rect(10, 150, config.PANEL_WIDTH - 20, 420)
        else:
            chart_rect = pygame.Rect(10, 150, config.PANEL_WIDTH - 20, 400)

        status_text = getattr(system, "status_text", "")
        status_color = getattr(system, "status_color", (0, 255, 100))
        draw_chart(gui_surface, chart_rect, font_small, charts)

    elif selected_mode == "SATELLITE":
        charts_data = system.get_charts_data()
        charts = [
            {"title": "Orientacja Satelity [deg]", "min_val": -180.0, "max_val": 180.0, "series": charts_data.get("satellite_chart", [])},
            {"title": "Predkosc Kola Zamachowego [rad/s]", "min_val": -system.max_wheel_speed, "max_val": system.max_wheel_speed, "series": charts_data.get("wheel_chart", [])},
        ]
        if "u_chart" in charts_data:
            charts.append({"title": "Moment Sterujacy M [Nm]", "min_val": -10.0, "max_val": 10.0, "series": charts_data["u_chart"]})
            chart_rect = pygame.Rect(10, 150, config.PANEL_WIDTH - 20, 380)
        else:
            chart_rect = pygame.Rect(10, 150, config.PANEL_WIDTH - 20, 320)

        status_text = getattr(system, "status_text", "")
        draw_chart(gui_surface, chart_rect, font_small, charts)

    elif selected_mode == "FURUTA":
        charts_data = system.get_charts_data()
        max_torque = getattr(system.controller, "max_torque", 5.0)

        charts = [
            {"title": "Kat Wahadla [deg]", "min_val": -180.0, "max_val": 180.0, "series": charts_data.get("pendulum_chart", [])},
            {"title": "Kat Ramienia i Zadany [deg]", "min_val": -180.0, "max_val": 180.0, "series": charts_data.get("arm_chart", [])},
            {"title": "Moment Sterujacy M [Nm]", "min_val": -max_torque, "max_val": max_torque, "series": charts_data.get("u_chart", [])}
        ]
        
        chart_rect = pygame.Rect(10, 210, config.PANEL_WIDTH - 20, 330)
        status_text = getattr(system, "status_text", "")
        status_color = getattr(system, "status_color", (0, 255, 100))
        draw_chart(gui_surface, chart_rect, font_small, charts)

    # RYSOWANIE STATUSU DOKŁADNIE 1 RAZ POD RAMKĄ WYKRESU
    if chart_rect and status_text:
        txt_surf = font_small.render(status_text, True, status_color)
        gui_surface.blit(txt_surf, (10, chart_rect.bottom + 10))