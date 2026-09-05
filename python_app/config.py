# config.py

# --- Okno i Widoki ---
WINDOW_WIDTH = 1250
WINDOW_HEIGHT = 720
VIEW3D_WIDTH = 980
PANEL_WIDTH = WINDOW_WIDTH - VIEW3D_WIDTH
FPS = 60

# --- Serial / IMU ---
SERIAL_PORT = 'COM8'
BAUD_RATE = 115200
SERIAL_TIMEOUT = 0.01

# --- Kolorystyka UI ---
COLOR_BG = (26, 30, 42)
COLOR_TEXT = (220, 220, 220)
COLOR_PANEL_BG = (32, 38, 52)
COLOR_PANEL_BORDER = (70, 80, 105)
COLOR_GRID_LINE = (50, 58, 78)
COLOR_LABEL_TEXT = (160, 172, 195)

COLOR_SLIDER_BG = (45, 52, 70)
COLOR_SLIDER_HANDLE = (0, 160, 255)
COLOR_SLIDER_BORDER = (255, 255, 255)

# Kolory przycisków (Buttons)
COLOR_BTN = (50, 60, 80)
COLOR_BTN_HOVER = (70, 85, 115)
COLOR_BTN_TEXT = (255, 255, 255)
COLOR_BTN_RESET = (180, 50, 50)
COLOR_BTN_RESET_HOVER = (220, 70, 70)

SLIDER_MIN_VAL = -10.0
SLIDER_MAX_VAL = 10.0

IMU_MEDIAN_WINDOW_SIZE = 5

# --- Parametry Suwnicy (Crane) ---
CRANE_PARAMS = {
    "m_cart": 2.0,     # Masa wózka [kg]
    "m_load": 0.8,     # Masa ładunku [kg]
    "length": 1.2,     # Długość liny [m]
    "g": 9.81,         # Przyspieszenie ziemskie [m/s^2]
    "x_limit": 2.0     # Dopuszczalny tor jazdy [m]
}

PID_CRANE_CONFIG = {
    "Kp_pos": 8.0,
    "Kd_pos": 5.0,
    "Kp_angle": 25.0,
    "Kd_angle": 10.0,
    "max_force": 30.0
}

# --- Parametry Wahadła Furuty ---
FURUTA_PARAMS = {
    "L_r": 0.25,             # Długość ramienia [m]
    "m_r": 0.20,             # Masa ramienia [kg]
    "J_r": 0.005,            # Moment bezwładności ramienia
    "L_p": 0.35,             # Długość wahadła [m]
    "m_p": 0.10,             # Masa wahadła [kg]
    "J_p": 0.003,            # Moment bezwładności wahadła
    "g": 9.81,               # Przyspieszenie ziemskie [m/s^2]
    "b_r": 0.05,             # Tłumienie ramienia
    "b_p": 0.01,             # Tłumienie wahadła
    "max_omega": 100.0,      # Maksymalna prędkość kątowa
    "initial_theta2": 0.01   # Początkowe wychylenie wahadła [rad]
}

LQR_FURUTA_CONFIG = {
    "max_torque": 2.5,                  # Maksymalny moment obrotowy [Nm]
    "initial_K": [-0.8, -0.5, 5.5, 0.8], # Domyślne wzmocnienia regulatora K_theta1, K_omega1, K_theta2, K_omega2
    "activation_angle_deg": 30.0        # Maksymalny kąt wychylenia wahadła od pionu (w stopniach)
}

# --- Parametry Quadrocoptera ---
QUAD_PARAMS = {
    "arm_len": 0.25,         # Długość ramienia [m]
    "filter_window": 5       # Okno filtra uśredniającego
}

PID_QUAD_CONFIG = {
    "Kp_default": 10.0,
    "Ki_default": 0.0,
    "Kd_default": 2.0,
    "limit_default": 15.0    # Limit wyjścia regulatora PID
}

# --- Parametry Ball & Plate System ---
BALL_PLATE_PARAMS = {
    "plate_size": 1.4,        # Połowa szerokości płytki [m]
    "plate_thickness": 0.05,  # Grubość płytki [m]
    "ball_radius": 0.09,      # Promień kuli [m]
    "g": 9.81,                # Przyspieszenie ziemskie [m/s^2]
    "damping": 1.2,           # Tłumienie oporów toczenia
    "restitution": 0.4        # Współczynnik odbicia od krawędzi (0-1)
}

PID_BALL_PLATE_CONFIG = {
    "Kp_default": 8.5,
    "Ki_default": 0.0,
    "Kd_default": 0.8,
    "limit_default": 18.0,    # Maksymalne wychylenie serwomechanizmów [deg]
    "integral_limit": 5.0     # Anty-windup dla całki
}

# --- Parametry Satelity (Satellite) ---
SATELLITE_CONFIG = {
    "I_sat": 2.5,                 # Moment bezwładności kadłuba [kg*m^2]
    "I_wheel": 0.3,               # Moment bezwładności koła zamachowego [kg*m^2]
    "max_wheel_speed": 100.0,     # Limit prędkości obrotowej koła [rad/s]
    "max_torque": 25.0,           # Maksymalny moment obrotowy [Nm]
    "Kp_default": 10.0,
    "Ki_default": 0.0,
    "Kd_default": 12.0,
    "integral_limit": 5.0
}