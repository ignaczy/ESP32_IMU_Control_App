import math
import numpy as np
from collections import deque
from models.base_system import BaseSystem
from ui.renderer_3d import draw_quadrocopter_scene
from ui.widgets import Button, Slider


class SafePID:
    def __init__(self, Kp, Ki, Kd, limit=15.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.limit = limit
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.last_measurement = None

    def update(self, setpoint, measurement, dt):
        if dt <= 0.0001:
            return 0.0

        error = setpoint - measurement

        if self.last_measurement is None:
            self.last_measurement = measurement

        self.integral += error * dt
        self.integral = max(-5.0, min(5.0, self.integral))

        d_measurement = (measurement - self.last_measurement) / dt
        self.last_measurement = measurement

        output = (self.Kp * error) + (self.Ki * self.integral) - (self.Kd * d_measurement)
        return max(-self.limit, min(self.limit, output))


class QuadrocopterSystem(BaseSystem):
    def __init__(self, config):
        super().__init__()
        self.config = config

        # Retrieve parameters from configuration
        quad_params = getattr(config, 'QUAD_PARAMS', {})
        pid_config = getattr(config, 'PID_QUAD_CONFIG', {})

        self.arm_len = quad_params.get("arm_len", getattr(config, 'QUAD_ARM_LEN', 0.25))
        self.g = 9.81

        self.Kp = pid_config.get("Kp_default", getattr(config, 'QUAD_KP_DEFAULT', 10.0))
        self.Ki = pid_config.get("Ki_default", getattr(config, 'QUAD_KI_DEFAULT', 0.0))
        self.Kd = pid_config.get("Kd_default", getattr(config, 'QUAD_KD_DEFAULT', 2.0))
        self.pid_limit = pid_config.get("limit_default", getattr(config, 'QUAD_PID_LIMIT', 15.0))

        self.pid_x = SafePID(Kp=self.Kp, Ki=self.Ki, Kd=self.Kd, limit=self.pid_limit)
        self.pid_y = SafePID(Kp=self.Kp, Ki=self.Ki, Kd=self.Kd, limit=self.pid_limit)

        # UI WIDGETS (slightly lowered and with Ki slider)
        self.slider_kp = Slider(20, 50, 220, 12, 0.0, 20.0, self.Kp, "Kp")
        self.slider_ki = Slider(20, 80, 220, 12, 0.0, 5.0, self.Ki, "Ki")
        self.slider_kd = Slider(20, 110, 220, 12, 0.0, 10.0, self.Kd, "Kd")
        self.btn_reset = Button(20, 140, 220, 25, "RESET STATE (SPACE)")

        # STATUS ATTRIBUTES
        self.status_text = "QUADROCOPTER ACTIVE"
        self.status_color = (0, 255, 100)

        # HISTORY BUFFERS FOR CHARTS
        self.MAX_HIST = 150
        self.hist_sp_x = deque(maxlen=self.MAX_HIST)
        self.hist_pv_x = deque(maxlen=self.MAX_HIST)
        self.hist_sp_y = deque(maxlen=self.MAX_HIST)
        self.hist_pv_y = deque(maxlen=self.MAX_HIST)
        self.hist_roll = deque(maxlen=self.MAX_HIST)
        self.hist_pitch = deque(maxlen=self.MAX_HIST)
        
        # Control signal buffers
        self.hist_u_roll = deque(maxlen=self.MAX_HIST)
        self.hist_u_pitch = deque(maxlen=self.MAX_HIST)

        self.setpoint_x = 0.0
        self.setpoint_y = 0.0
        self.reset_state()

    def reset_state(self):
        self.pos = [0.0, 0.0, 0.8]
        self.vel = [0.0, 0.0]
        self.phi = 0.0
        self.theta = 0.0
        self.prop_angle = 0.0
        self.setpoint_x = 0.0
        self.setpoint_y = 0.0

        self.pid_x.reset()
        self.pid_y.reset()

        self.hist_sp_x.clear()
        self.hist_pv_x.clear()
        self.hist_sp_y.clear()
        self.hist_pv_y.clear()
        self.hist_roll.clear()
        self.hist_pitch.clear()
        self.hist_u_roll.clear()
        self.hist_u_pitch.clear()

        # Fill with default zeros
        self.hist_sp_x.extend([0.0] * self.MAX_HIST)
        self.hist_pv_x.extend([0.0] * self.MAX_HIST)
        self.hist_sp_y.extend([0.0] * self.MAX_HIST)
        self.hist_pv_y.extend([0.0] * self.MAX_HIST)
        self.hist_roll.extend([0.0] * self.MAX_HIST)
        self.hist_pitch.extend([0.0] * self.MAX_HIST)
        self.hist_u_roll.extend([0.0] * self.MAX_HIST)
        self.hist_u_pitch.extend([0.0] * self.MAX_HIST)

        self.update_status()

    def reset(self):
        self.reset_state()

    def update_params(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.pid_x.Kp = self.pid_y.Kp = Kp
        self.pid_x.Ki = self.pid_y.Ki = Ki
        self.pid_x.Kd = self.pid_y.Kd = Kd

    def update_status(self):
        """Updates status text attributes."""
        self.status_text = f"QUADROCOPTER ACTIVE | Pos: X={self.pos[0]:.2f}m, Y={self.pos[1]:.2f}m"
        self.status_color = (0, 255, 100)

    def set_target_from_input(self, norm_x, norm_y=0.5):
        self.setpoint_x = (norm_x - 0.5) * 4.0
        self.setpoint_y = (norm_y - 0.5) * 4.0

    def process_serial_data(self, roll, pitch):
        self.setpoint_x = max(-2.0, min(2.0, (roll / 45.0) * 2.0))
        self.setpoint_y = max(-2.0, min(2.0, (pitch / 45.0) * 2.0))

    def step(self, dt):
        # Fetch values from all 3 sliders
        self.update_params(self.slider_kp.val, self.slider_ki.val, self.slider_kd.val)

        if dt <= 0.0001:
            return math.degrees(self.phi), math.degrees(self.theta)

        # Calculate control signals (desired roll/pitch angles)
        target_roll = self.pid_x.update(self.setpoint_x, self.pos[0], dt)
        target_pitch = self.pid_y.update(self.setpoint_y, self.pos[1], dt)

        target_phi = math.radians(target_roll)
        target_theta = math.radians(target_pitch)

        self.phi += (target_phi - self.phi) * (dt / (0.04 + dt))
        self.theta += (target_theta - self.theta) * (dt / (0.04 + dt))

        ax = self.g * math.sin(self.phi) - 3.0 * self.vel[0]
        ay = self.g * math.sin(self.theta) - 3.0 * self.vel[1]

        self.vel[0] += ax * dt
        self.vel[1] += ay * dt

        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt

        self.prop_angle = (self.prop_angle + 1200 * dt) % 360

        # Update history
        self.hist_sp_x.append(self.setpoint_x)
        self.hist_pv_x.append(self.pos[0])
        self.hist_sp_y.append(self.setpoint_y)
        self.hist_pv_y.append(self.pos[1])
        self.hist_roll.append(math.degrees(self.phi))
        self.hist_pitch.append(math.degrees(self.theta))
        self.hist_u_roll.append(target_roll)
        self.hist_u_pitch.append(target_pitch)

        self.update_status()

        return target_roll, target_pitch

    def get_widgets(self):
        return [self.slider_kp, self.slider_ki, self.slider_kd, self.btn_reset]

    def get_charts_data(self):
        return {
            "pos_x_chart": [
                {"data": list(self.hist_sp_x), "color": (80, 220, 120)},
                {"data": list(self.hist_pv_x), "color": (100, 200, 255)},
            ],
            "pos_y_chart": [
                {"data": list(self.hist_sp_y), "color": (80, 220, 120)},
                {"data": list(self.hist_pv_y), "color": (200, 100, 255)},
            ],
            "u_chart": [
                {"data": list(self.hist_u_roll), "color": (255, 140, 0)},
                {"data": list(self.hist_u_pitch), "color": (0, 220, 220)},
            ],
            "status_text": self.status_text,
            "status_color": self.status_color,
        }

    def draw_3d(self):
        draw_quadrocopter_scene(self)

    def render_3d(self):
        self.draw_3d()