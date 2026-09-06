import math
from collections import deque
import config
from ui.widgets import Slider, Button


class CranePID:
    def __init__(self, Kp_pos=4.0, Kd_pos=2.0, Kp_angle=15.0, Kd_angle=3.0, max_force=30.0):
        self.Kp_pos = Kp_pos
        self.Kd_pos = Kd_pos
        self.Kp_angle = Kp_angle
        self.Kd_angle = Kd_angle
        self.max_force = max_force

    def update(self, target_x, cart_x, cart_vx, pendulum_angle, pendulum_omega, dt):
        if dt <= 0.0001:
            return 0.0

        pos_error = target_x - cart_x
        f_pos = (self.Kp_pos * pos_error) - (self.Kd_pos * cart_vx)
        f_angle = (self.Kp_angle * pendulum_angle) + (self.Kd_angle * pendulum_omega)
        total_force = f_pos + f_angle

        return max(-self.max_force, min(self.max_force, total_force))


class CraneSystem:
    def __init__(self, cfg=config):
        self.m_cart = cfg.CRANE_PARAMS["m_cart"]
        self.m_load = cfg.CRANE_PARAMS["m_load"]
        self.length = cfg.CRANE_PARAMS["length"]
        self.g = cfg.CRANE_PARAMS["g"]
        self.x_limit = cfg.CRANE_PARAMS["x_limit"]

        # PID controller initialization
        pid_cfg = getattr(cfg, "PID_CRANE_CONFIG", {
            "Kp_pos": 4.0,
            "Kd_pos": 2.0,
            "Kp_angle": 15.0,
            "Kd_angle": 3.0
        })
        
        if "initial_K" in pid_cfg:
            k = pid_cfg["initial_K"]
            self.pid = CranePID(Kp_pos=k[0], Kd_pos=k[1], Kp_angle=k[2], Kd_angle=k[3])
        else:
            self.pid = CranePID(**pid_cfg)

        # STATUS ATTRIBUTES
        self.status_text = "CRANE ACTIVE"
        self.status_color = (200, 200, 200)

        # SLIDERS
        self.slider_pos_kp = Slider(20, 80, 200, 10, 0.0, 20.0, self.pid.Kp_pos, "Kp Position", step=0.1)
        self.slider_pos_kd = Slider(20, 120, 200, 10, 0.0, 10.0, self.pid.Kd_pos, "Kd Position", step=0.1)
        self.slider_sway_kp = Slider(20, 160, 200, 10, 0.0, 50.0, self.pid.Kp_angle, "Kp Anti-Sway", step=0.1)
        self.slider_sway_kd = Slider(20, 200, 200, 10, 0.0, 20.0, self.pid.Kd_angle, "Kd Anti-Sway", step=0.1)

        self.btn_reset = Button(20, 240, 200, 24, "RESET STATE (SPACE)")

        self.setpoint_x = 0.0

        # Internal history buffers for charts
        self.max_hist = 150
        self.hist_target_x = deque(maxlen=self.max_hist)
        self.hist_cart_x = deque(maxlen=self.max_hist)
        self.hist_sway_angle = deque(maxlen=self.max_hist)
        self.hist_u = deque(maxlen=self.max_hist)  # Buffer for control signal (force)

        self.reset_state()

    def update_status(self):
        """Updates status text and color."""
        self.status_text = f"CRANE ACTIVE | Pos: X={self.x:.2f}m | Sway: {math.degrees(self.theta):.1f}°"
        self.status_color = (0, 255, 100)

    def reset_state(self):
        self.x = 0.0
        self.vx = 0.0
        self.theta = 0.0
        self.omega = 0.0
        self.setpoint_x = 0.0
        self.hist_target_x.clear()
        self.hist_cart_x.clear()
        self.hist_sway_angle.clear()
        self.hist_u.clear()  # Clear control buffer on reset
        self.update_status()

    def reset(self):
        self.reset_state()

    def set_target_from_input(self, norm_x, norm_y=None):
        """Sets target position of the cart based on a click in the 3D view."""
        self.setpoint_x = (norm_x - 0.5) * 4.0

    def process_serial_data(self, roll, pitch):
        """Sets target position from IMU controller (roll angle)."""
        self.setpoint_x = max(-2.0, min(2.0, (roll / 45.0) * 2.0))

    def step(self, dt):
        if dt <= 0.0001:
            return

        # Update controller parameters from widgets
        self.pid.Kp_pos = self.slider_pos_kp.val
        self.pid.Kd_pos = self.slider_pos_kd.val
        self.pid.Kp_angle = self.slider_sway_kp.val
        self.pid.Kd_angle = self.slider_sway_kd.val

        # Calculate force from PID controller
        force = self.pid.update(
            self.setpoint_x, self.x, self.vx, self.theta, self.omega, dt
        )

        # Equations of motion for crane with pendulum
        sin_t = math.sin(self.theta)
        cos_t = math.cos(self.theta)

        M_total = self.m_cart + self.m_load

        alpha = (-self.g * sin_t - (force / M_total) * cos_t) / self.length
        ax = (force + self.m_load * self.length * alpha * cos_t) / M_total

        self.vx += ax * dt
        self.omega += alpha * dt

        # Damping / resistance
        self.vx *= 0.98
        self.omega *= 0.985

        self.x += self.vx * dt
        self.theta += self.omega * dt

        # Rail track limits
        if abs(self.x) > self.x_limit:
            self.x = math.copysign(self.x_limit, self.x)
            self.vx = -self.vx * 0.2

        # Record to history buffers for charts
        self.hist_target_x.append(self.setpoint_x)
        self.hist_cart_x.append(self.x)
        self.hist_sway_angle.append(math.degrees(self.theta))
        self.hist_u.append(force)  # Record calculated control force F

        # Update status field
        self.update_status()

    def get_widgets(self):
        """Returns a list of interface control widgets."""
        return [
            self.slider_pos_kp, 
            self.slider_pos_kd, 
            self.slider_sway_kp, 
            self.slider_sway_kd, 
            self.btn_reset
        ]

    def get_charts_data(self):
        """Returns a dictionary of data required to generate charts in the panel."""
        return {
            "pos_chart": [
                {"data": list(self.hist_target_x), "color": (50, 220, 130)},
                {"data": list(self.hist_cart_x), "color": (80, 170, 255)},
            ],
            "sway_chart": [
                {"data": list(self.hist_sway_angle), "color": (255, 90, 90)},
            ],
            "u_chart": [
                {"data": list(self.hist_u), "color": (255, 200, 80)},
            ]
        }