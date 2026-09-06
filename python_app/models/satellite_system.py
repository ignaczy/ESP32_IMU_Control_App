import math
from collections import deque
from models.base_system import BaseSystem
from ui.renderer_3d import draw_satellite_scene
from ui.widgets import Button, Slider


def angle_difference(target, current):
    """Calculates the minimal angular difference wrapped to [-pi, pi]."""
    return (target - current + math.pi) % (2 * math.pi) - math.pi


def normalize_angle(angle):
    """Normalizes an angle to the range [-pi, pi]."""
    return (angle + math.pi) % (2 * math.pi) - math.pi


class SatellitePID:
    def __init__(self, Kp=10.0, Ki=0.0, Kd=12.0, max_torque=25.0, integral_limit=5.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.max_torque = max_torque
        self.integral_limit = integral_limit
        self.reset()

    def reset(self):
        self.integral = 0.0

    def compute(self, setpoint_angle, sat_angle, sat_omega, dt):
        if dt <= 0.0001:
            return 0.0

        error = angle_difference(setpoint_angle, sat_angle)
        self.integral += error * dt
        self.integral = max(-self.integral_limit, min(self.integral_limit, self.integral))

        output = (self.Kp * error) + (self.Ki * self.integral) - (self.Kd * sat_omega)
        return max(-self.max_torque, min(self.max_torque, output))


class SatelliteSystem(BaseSystem):
    def __init__(self, config=None):
        super().__init__()
        self.config = config

        sat_cfg = getattr(config, 'SATELLITE_CONFIG', {}) if config else {}

        self.I_sat = sat_cfg.get("I_sat", getattr(config, 'I_SAT', 2.5))
        self.I_wheel = sat_cfg.get("I_wheel", getattr(config, 'I_WHEEL', 0.3))
        self.max_wheel_speed = sat_cfg.get("max_wheel_speed", getattr(config, 'MAX_WHEEL_SPEED', 100.0))
        
        kp = sat_cfg.get("Kp_default", getattr(config, 'SATELLITE_KP_DEFAULT', 10.0))
        ki = sat_cfg.get("Ki_default", getattr(config, 'SATELLITE_KI_DEFAULT', 0.0))
        kd = sat_cfg.get("Kd_default", getattr(config, 'SATELLITE_KD_DEFAULT', 12.0))
        max_torque = sat_cfg.get("max_torque", getattr(config, 'SATELLITE_MAX_TORQUE', 25.0))
        integral_limit = sat_cfg.get("integral_limit", getattr(config, 'SATELLITE_INTEGRAL_LIMIT', 5.0))

        self.pid = SatellitePID(
            Kp=kp, Ki=ki, Kd=kd,
            max_torque=max_torque, integral_limit=integral_limit
        )

        self.angle_sat = 0.0
        self.omega_sat = 0.0
        self.angle_wheel = 0.0
        self.omega_wheel = 0.0

        self.setpoint_angle = 0.0
        self.current_torque = 0.0

        # Internal status
        self.status_text = "SATELLITE ACTIVE"
        self.status_color = (0, 255, 100)

        self.max_hist = 150
        self.hist_sp = deque([0.0] * self.max_hist, maxlen=self.max_hist)
        self.hist_pv = deque([0.0] * self.max_hist, maxlen=self.max_hist)
        self.hist_wheel_speed = deque([0.0] * self.max_hist, maxlen=self.max_hist)
        self.hist_u = deque([0.0] * self.max_hist, maxlen=self.max_hist)

        # Widget initialization (Ki slider added, Kd and Button moved down)
        self.slider_kp = Slider(20, 35, 220, 12, 0.0, 40.0, self.pid.Kp, "Kp")
        self.slider_ki = Slider(20, 70, 220, 12, 0.0, 10.0, self.pid.Ki, "Ki")
        self.slider_kd = Slider(20, 105, 220, 12, 0.0, 30.0, self.pid.Kd, "Kd")
        self.btn_reset = Button(20, 135, 220, 25, "RESET STATE (SPACE)")

        self.update_status()

    def update_status(self):
        """Updates status attributes."""
        self.status_text = f"SATELLITE | Angle: {math.degrees(self.angle_sat):.1f} deg | Wheel: {self.omega_wheel:.1f} rad/s"
        self.status_color = (0, 255, 100)

    def reset_state(self):
        self.reset()

    def reset(self):
        self.angle_sat = 0.0
        self.omega_sat = 0.0
        self.angle_wheel = 0.0
        self.omega_wheel = 0.0
        self.setpoint_angle = 0.0
        self.current_torque = 0.0
        self.pid.reset()
        self.hist_sp.clear()
        self.hist_pv.clear()
        self.hist_wheel_speed.clear()
        self.hist_u.clear()
        self.hist_sp.extend([0.0] * self.max_hist)
        self.hist_pv.extend([0.0] * self.max_hist)
        self.hist_wheel_speed.extend([0.0] * self.max_hist)
        self.hist_u.extend([0.0] * self.max_hist)
        self.update_status()

    def update_params(self, Kp, Ki, Kd):
        self.pid.Kp = Kp
        self.pid.Ki = Ki
        self.pid.Kd = Kd

    def set_target_from_input(self, norm_x, norm_y=0.5):
        self.setpoint_angle = normalize_angle((norm_x - 0.5) * 2.0 * math.pi)

    def update(self, dt):
        self.step(dt)

    def step(self, dt):
        if dt <= 0.0001:
            return

        # Update controller parameters from sliders (including Ki gain)
        self.update_params(self.slider_kp.val, self.slider_ki.val, self.slider_kd.val)

        self.current_torque = self.pid.compute(self.setpoint_angle, self.angle_sat, self.omega_sat, dt)
        torque = self.current_torque

        abs_wheel_omega = self.omega_sat + self.omega_wheel
        if (abs_wheel_omega >= self.max_wheel_speed and torque > 0) or \
           (abs_wheel_omega <= -self.max_wheel_speed and torque < 0):
            torque = 0.0

        alpha_sat = torque / self.I_sat
        alpha_wheel_rel = -(torque / self.I_wheel) - alpha_sat

        self.omega_sat += alpha_sat * dt
        self.omega_wheel += alpha_wheel_rel * dt

        bearing_friction = 0.01 * self.omega_wheel
        self.omega_sat -= (bearing_friction / self.I_sat) * dt
        self.omega_wheel += (bearing_friction / self.I_wheel) * dt

        self.angle_sat += self.omega_sat * dt
        self.angle_wheel += self.omega_wheel * dt
        self.angle_sat = normalize_angle(self.angle_sat)

        self.hist_sp.append(math.degrees(self.setpoint_angle))
        self.hist_pv.append(math.degrees(self.angle_sat))
        self.hist_wheel_speed.append(self.omega_wheel)
        self.hist_u.append(self.current_torque)

        self.update_status()

    def get_widgets(self):
        return [self.slider_kp, self.slider_ki, self.slider_kd, self.btn_reset]

    def get_charts_data(self):
        return {
            "satellite_chart": [
                {"data": list(self.hist_sp), "color": (80, 220, 120)},
                {"data": list(self.hist_pv), "color": (255, 180, 50)}
            ],
            "wheel_chart": [
                {"data": list(self.hist_wheel_speed), "color": (100, 200, 255)}
            ],
            "u_chart": [
                {"data": list(self.hist_u), "color": (255, 180, 80)}
            ]
        }

    def render_3d(self):
        draw_satellite_scene(self)

    def draw_3d(self):
        self.render_3d()