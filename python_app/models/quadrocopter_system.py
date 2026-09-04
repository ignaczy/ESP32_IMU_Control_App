import math
from collections import deque
from statistics import median
from models.base_system import BaseSystem
from ui.renderer_3d import draw_quadrocopter_scene


class MedianFilter:
    def __init__(self, window_size=5):
        self.buffer_roll = deque(maxlen=window_size)
        self.buffer_pitch = deque(maxlen=window_size)

    def filter(self, raw_roll, raw_pitch):
        self.buffer_roll.append(raw_roll)
        self.buffer_pitch.append(raw_pitch)
        return median(self.buffer_roll), median(self.buffer_pitch)


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
        
        # Pobieranie parametrów ze słowników lub zmiennych z config.py
        quad_params = getattr(config, 'QUAD_PARAMS', {})
        pid_config = getattr(config, 'PID_QUAD_CONFIG', {})

        self.arm_len = quad_params.get("arm_len", getattr(config, 'QUAD_ARM_LEN', 0.25))
        window_size = quad_params.get("filter_window", getattr(config, 'QUAD_FILTER_WINDOW', 5))
        
        self.g = 9.81
        self.median_filter = MedianFilter(window_size=window_size)
        
        kp = pid_config.get("Kp_default", getattr(config, 'QUAD_KP_DEFAULT', 10.0))
        ki = pid_config.get("Ki_default", getattr(config, 'QUAD_KI_DEFAULT', 0.0))
        kd = pid_config.get("Kd_default", getattr(config, 'QUAD_KD_DEFAULT', 2.0))
        limit = pid_config.get("limit_default", getattr(config, 'QUAD_PID_LIMIT', 15.0))

        self.pid_x = SafePID(Kp=kp, Ki=ki, Kd=kd, limit=limit)
        self.pid_y = SafePID(Kp=kp, Ki=ki, Kd=kd, limit=limit)
        
        self.setpoint_x = 0.0
        self.setpoint_y = 0.0
        self.reset_state()

    def reset_state(self):
        self.pos = [0.0, 0.0, 0.8]
        self.vel = [0.0, 0.0]
        self.phi = 0.0
        self.theta = 0.0
        self.prop_angle = 0.0
        self.pid_x.reset()
        self.pid_y.reset()

    def update_params(self, Kp, Kd, Ki=0.0):
        self.pid_x.Kp = self.pid_y.Kp = Kp
        self.pid_x.Kd = self.pid_y.Kd = Kd
        self.pid_x.Ki = self.pid_y.Ki = Ki

    def process_serial_data(self, raw_roll, raw_pitch):
        filt_roll, filt_pitch = self.median_filter.filter(raw_roll, raw_pitch)
        self.setpoint_x = max(-2.0, min(2.0, (filt_roll / 45.0) * 2.0))
        self.setpoint_y = max(-2.0, min(2.0, (filt_pitch / 45.0) * 2.0))

    def step(self, dt):
        if dt <= 0.0001:
            return

        target_roll = self.pid_x.update(self.setpoint_x, self.pos[0], dt)
        target_pitch = -self.pid_y.update(self.setpoint_y, self.pos[1], dt)

        target_phi = math.radians(target_roll)
        target_theta = math.radians(target_pitch)

        self.phi += (target_phi - self.phi) * (dt / (0.04 + dt))
        self.theta += (target_theta - self.theta) * (dt / (0.04 + dt))

        ax = self.g * math.tan(self.phi) - 3.0 * self.vel[0]
        ay = -self.g * math.tan(self.theta) - 3.0 * self.vel[1]

        self.vel[0] += ax * dt
        self.vel[1] += ay * dt

        self.pos[0] += self.vel[0] * dt
        self.pos[1] += self.vel[1] * dt

        self.prop_angle = (self.prop_angle + 1200 * dt) % 360
        
        return target_roll, target_pitch

    def draw_3d(self):
        draw_quadrocopter_scene(self)

    def render_3d(self):
        """Alias dla draw_3d zapewniający zgodność z pętlą główną main.py."""
        self.draw_3d()

    def reset(self):
        self.reset_state()

    def set_target_from_input(self, norm_x):
        self.setpoint_x = (norm_x - 0.5) * 4.0

    def get_widgets(self):
        return []

    def get_charts_data(self):
        return {
            "pendulum_chart": [],
            "arm_chart": [],
            "status_text": f"Pos: X={self.pos[0]:.2f}m, Y={self.pos[1]:.2f}m",
            "status_color": (0, 255, 100)
        }