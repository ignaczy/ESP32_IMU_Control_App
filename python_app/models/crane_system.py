# models/crane_system.py

import math
import config

class CranePID:
    def __init__(self, Kp_pos, Kd_pos, Kp_angle, Kd_angle, max_force=30.0):
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
    def __init__(self):
        self.m_cart = config.CRANE_PARAMS["m_cart"]
        self.m_load = config.CRANE_PARAMS["m_load"]
        self.length = config.CRANE_PARAMS["length"]
        self.g = config.CRANE_PARAMS["g"]
        self.x_limit = config.CRANE_PARAMS["x_limit"]
        self.reset_state()

    def reset_state(self):
        self.x = 0.0
        self.vx = 0.0
        self.theta = 0.0
        self.omega = 0.0
        
    def reset(self):
        self.x = 0.0
        self.vx = 0.0
        self.theta = 0.0
        self.omega = 0.0

    def step(self, force, dt):
        if dt <= 0.0001:
            return

        sin_t = math.sin(self.theta)
        cos_t = math.cos(self.theta)
        
        M_total = self.m_cart + self.m_load

        alpha = (-self.g * sin_t - (force / M_total) * cos_t) / self.length
        ax = (force + self.m_load * self.length * alpha * cos_t) / M_total

        self.vx += ax * dt
        self.omega += alpha * dt

        # Opory
        self.vx *= 0.98
        self.omega *= 0.985

        self.x += self.vx * dt
        self.theta += self.omega * dt

        if abs(self.x) > self.x_limit:
            self.x = math.copysign(self.x_limit, self.x)
            self.vx = -self.vx * 0.2