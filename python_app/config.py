# config.py

# --- Window and Views ---
WINDOW_WIDTH = 1250
WINDOW_HEIGHT = 720
VIEW3D_WIDTH = 980
PANEL_WIDTH = WINDOW_WIDTH - VIEW3D_WIDTH
FPS = 60

# --- Serial / IMU ---
SERIAL_PORT = 'COM8'
BAUD_RATE = 115200
SERIAL_TIMEOUT = 0.01

# --- UI Color Palette ---
COLOR_BG = (26, 30, 42)
COLOR_TEXT = (220, 220, 220)
COLOR_PANEL_BG = (32, 38, 52)
COLOR_PANEL_BORDER = (70, 80, 105)
COLOR_GRID_LINE = (50, 58, 78)
COLOR_LABEL_TEXT = (160, 172, 195)

COLOR_SLIDER_BG = (45, 52, 70)
COLOR_SLIDER_HANDLE = (0, 160, 255)
COLOR_SLIDER_BORDER = (255, 255, 255)

# Button Colors
COLOR_BTN = (50, 60, 80)
COLOR_BTN_HOVER = (70, 85, 115)
COLOR_BTN_TEXT = (255, 255, 255)
COLOR_BTN_RESET = (180, 50, 50)
COLOR_BTN_RESET_HOVER = (220, 70, 70)

SLIDER_MIN_VAL = -10.0
SLIDER_MAX_VAL = 10.0

IMU_MEDIAN_WINDOW_SIZE = 5

# --- Crane Parameters ---
CRANE_PARAMS = {
    "m_cart": 2.0,     # Cart mass [kg]
    "m_load": 0.8,     # Payload mass [kg]
    "length": 1.2,     # Cable length [m]
    "g": 9.81,         # Gravitational acceleration [m/s^2]
    "x_limit": 2.0     # Allowed rail travel distance [m]
}

PID_CRANE_CONFIG = {
    "Kp_pos": 8.0,
    "Kd_pos": 5.0,
    "Kp_angle": 25.0,
    "Kd_angle": 10.0,
    "max_force": 30.0
}

# --- Furuta Pendulum Parameters ---
FURUTA_PARAMS = {
    "L_r": 0.25,             # Arm length [m]
    "m_r": 0.20,             # Arm mass [kg]
    "J_r": 0.005,            # Arm moment of inertia
    "L_p": 0.35,             # Pendulum length [m]
    "m_p": 0.10,             # Pendulum mass [kg]
    "J_p": 0.003,            # Pendulum moment of inertia
    "g": 9.81,               # Gravitational acceleration [m/s^2]
    "b_r": 0.05,             # Arm damping
    "b_p": 0.01,             # Pendulum damping
    "max_omega": 100.0,      # Maximum angular velocity
    "initial_theta2": 0.01   # Initial pendulum angle displacement [rad]
}

LQR_FURUTA_CONFIG = {
    "max_torque": 2.5,                  # Maximum torque [Nm]
    "initial_K": [-0.8, -0.5, 5.5, 0.8], # Default controller gains: K_theta1, K_omega1, K_theta2, K_omega2
    "activation_angle_deg": 30.0        # Maximum pendulum deflection angle from upright position (in degrees)
}

# --- Quadrocopter Parameters ---
QUAD_PARAMS = {
    "arm_len": 0.25,         # Arm length [m]
    "filter_window": 5       # Moving average filter window size
}

PID_QUAD_CONFIG = {
    "Kp_default": 10.0,
    "Ki_default": 0.0,
    "Kd_default": 2.0,
    "limit_default": 15.0    # PID controller output limit
}

# --- Ball & Plate System Parameters ---
BALL_PLATE_PARAMS = {
    "plate_size": 1.4,        # Half-width of the plate [m]
    "plate_thickness": 0.05,  # Plate thickness [m]
    "ball_radius": 0.09,      # Ball radius [m]
    "g": 9.81,                # Gravitational acceleration [m/s^2]
    "damping": 1.2,           # Rolling resistance damping
    "restitution": 0.4        # Coefficient of restitution for edge collisions (0-1)
}

PID_BALL_PLATE_CONFIG = {
    "Kp_default": 8.5,
    "Ki_default": 0.0,
    "Kd_default": 0.8,
    "limit_default": 18.0,    # Maximum servo tilt angle [deg]
    "integral_limit": 5.0     # Anti-windup limit for integral term
}

# --- Satellite Parameters ---
SATELLITE_CONFIG = {
    "I_sat": 2.5,                 # Satellite body moment of inertia [kg*m^2]
    "I_wheel": 0.3,               # Reaction wheel moment of inertia [kg*m^2]
    "max_wheel_speed": 100.0,     # Maximum reaction wheel rotational speed [rad/s]
    "max_torque": 25.0,           # Maximum torque [Nm]
    "Kp_default": 10.0,
    "Ki_default": 0.0,
    "Kd_default": 12.0,
    "integral_limit": 5.0
}