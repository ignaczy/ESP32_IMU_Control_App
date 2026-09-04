import math
from collections import deque
from models.base_system import BaseSystem
from ui.renderer_3d import draw_satellite_scene


def angle_difference(target, current):
    return (target - current + math.pi) % (2 * math.pi) - math.pi


def normalize_angle(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


class SatellitePID:
    def __init__(self, Kp=10.0, Ki=0.0, Kd=12.0, max_torque=25.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.max_torque = max_torque
        self.reset()

    def reset(self):
        self.integral = 0.0

    def compute(self, setpoint_angle, sat_angle, sat_omega, dt):
        if dt <= 0.0001:
            return 0.0

        error = angle_difference(setpoint_angle, sat_angle)
        self.integral += error * dt
        self.integral = max(-5.0, min(5.0, self.integral))

        output = (self.Kp * error) + (self.Ki * self.integral) - (self.Kd * sat_omega)
        return max(-self.max_torque, min(self.max_torque, output))


class SatelliteSystem(BaseSystem):
    def __init__(self):
        super().__init__()
        # Parametry fizyczne
        self.I_sat = 2.5        # Moment bezwładności kadłuba [kg*m^2]
        self.I_wheel = 0.3      # Moment bezwładności koła zamachowego [kg*m^2]
        self.max_wheel_speed = 300.0

        # Stan
        self.angle_sat = 0.0
        self.omega_sat = 0.0
        self.angle_wheel = 0.0
        self.omega_wheel = 0.0

        self.setpoint_angle = 0.0
        self.pid = SatellitePID(Kp=10.0, Ki=0.0, Kd=12.0, max_torque=25.0)
        self.current_torque = 0.0

        # Historia
        self.max_hist = 150
        self.hist_sp = deque([0.0] * self.max_hist, maxlen=self.max_hist)
        self.hist_pv = deque([0.0] * self.max_hist, maxlen=self.max_hist)
        self.hist_wheel_speed = deque([0.0] * self.max_hist, maxlen=self.max_hist)

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
        self.hist_sp.extend([0.0] * self.max_hist)
        self.hist_pv.extend([0.0] * self.max_hist)
        self.hist_wheel_speed.extend([0.0] * self.max_hist)

    def set_target_from_input(self, norm_x, norm_y=0.5):
        self.setpoint_angle = normalize_angle((norm_x - 0.5) * 2.0 * math.pi)

    def update(self, dt):
        self.step(dt)

    def step(self, dt):
        if dt <= 0.0001:
            return

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

    def get_widgets(self):
        return []

    def get_charts_data(self):
        return {
            "pendulum_chart": [
                {"data": list(self.hist_sp), "color": (80, 220, 120)},
                {"data": list(self.hist_pv), "color": (100, 200, 255)}
            ],
            "arm_chart": [
                {"data": list(self.hist_wheel_speed), "color": (255, 180, 80)}
            ],
            "status_text": f"Kat Satelity: {math.degrees(self.angle_sat):.1f} deg | Kola: {self.omega_wheel:.1f} rad/s",
            "status_color": (230, 235, 245)
        }

    def render_3d(self):
        draw_satellite_scene(self)

    def draw_3d(self):
        self.render_3d()