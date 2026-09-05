import math
from collections import deque
from models.base_system import BaseSystem
from ui.widgets import Slider, Button
from ui.renderer_3d import draw_furuta_3d
import config


def normalize_angle(angle):
    """Sprowadza kąt do przedziału [-pi, pi]"""
    return (angle + math.pi) % (2 * math.pi) - math.pi


def angle_difference(target, current):
    return normalize_angle(target - current)


class FurutaPendulumPhysics:
    def __init__(self):
        params = config.FURUTA_PARAMS
        self.L_r = params["L_r"]
        self.m_r = params["m_r"]
        self.J_r = params["J_r"]
        self.L_p = params["L_p"]
        self.m_p = params["m_p"]
        self.J_p = params["J_p"]
        self.g = params["g"]
        self.b_r = params["b_r"]
        self.b_p = params["b_p"]
        self.max_omega = params["max_omega"]
        self.reset()

    def reset(self):
        self.theta1 = 0.0
        self.omega1 = 0.0
        self.theta2 = config.FURUTA_PARAMS["initial_theta2"]
        self.omega2 = 0.0

    def step_single(self, torque, dt):
        th2 = self.theta2

        d11 = self.J_r + self.m_p * (self.L_r**2) + 0.25 * self.m_p * (self.L_p**2) * (math.sin(th2)**2)
        d12 = -0.5 * self.m_p * self.L_r * self.L_p * math.cos(th2)
        d21 = d12
        d22 = self.J_p + 0.25 * self.m_p * (self.L_p**2)

        detD = d11 * d22 - d12 * d21
        if abs(detD) < 1e-9:
            return

        c1 = (0.5 * self.m_p * (self.L_p**2) * math.sin(th2) * math.cos(th2) * self.omega1 * self.omega2 
              + 0.5 * self.m_p * self.L_r * self.L_p * math.sin(th2) * (self.omega2**2))
        c2 = -0.25 * self.m_p * (self.L_p**2) * math.sin(th2) * math.cos(th2) * (self.omega1**2)
        g2 = 0.5 * self.m_p * self.g * self.L_p * math.sin(th2)

        f1 = torque - self.b_r * self.omega1 - c1
        f2 = -self.b_p * self.omega2 - c2 + g2

        alpha1 = (d22 * f1 - d12 * f2) / detD
        alpha2 = (-d21 * f1 + d11 * f2) / detD

        self.omega1 += alpha1 * dt
        self.omega2 += alpha2 * dt

        self.omega1 = max(-self.max_omega, min(self.max_omega, self.omega1))
        self.omega2 = max(-self.max_omega, min(self.max_omega, self.omega2))

        self.theta1 += self.omega1 * dt
        self.theta2 += self.omega2 * dt

        self.theta1 = normalize_angle(self.theta1)
        self.theta2 = normalize_angle(self.theta2)

    def step(self, torque, dt):
        if dt <= 0:
            return
        dt_sub = 0.0005
        steps = max(1, int(dt / dt_sub))
        actual_dt = dt / steps
        for _ in range(steps):
            self.step_single(torque, actual_dt)


class LQRController:
    def __init__(self, pendulum: FurutaPendulumPhysics):
        self.p = pendulum
        cfg = config.LQR_FURUTA_CONFIG
        self.max_torque = cfg["max_torque"]
        self.K = list(cfg["initial_K"])
        self.activation_angle = math.radians(cfg["activation_angle_deg"])
        self.active = True

    def update(self, setpoint_arm):
        th1 = self.p.theta1
        om1 = self.p.omega1
        th2 = self.p.theta2
        om2 = self.p.omega2

        if abs(th2) > self.activation_angle:
            self.active = False
            return 0.0

        self.active = True
        err_th1 = angle_difference(th1, setpoint_arm)

        u = -(self.K[0] * err_th1 + 
              self.K[1] * om1 + 
              self.K[2] * th2 + 
              self.K[3] * om2)

        return max(-self.max_torque, min(self.max_torque, u))


class FurutaSystem(BaseSystem):
    def __init__(self):
        super().__init__()
        self.physics = FurutaPendulumPhysics()
        self.controller = LQRController(self.physics)
        self.setpoint_arm = 0.0

        # Dodatkowe pola dla poprawnego odczytu statusu w rendererze
        self.status_text = ""
        self.status_color = (0, 255, 100)

        self.sliders = [
            Slider(20, 40, 200, 10, config.SLIDER_MIN_VAL, config.SLIDER_MAX_VAL, self.controller.K[0], "K_theta1 (Ramie pos)", step=0.1),
            Slider(20, 75, 200, 10, config.SLIDER_MIN_VAL, config.SLIDER_MAX_VAL, self.controller.K[1], "K_omega1 (Ramie vel)", step=0.1),
            Slider(20, 110, 200, 10, config.SLIDER_MIN_VAL, config.SLIDER_MAX_VAL, self.controller.K[2], "K_theta2 (Wahadlo pos)", step=0.1),
            Slider(20, 145, 200, 10, config.SLIDER_MIN_VAL, config.SLIDER_MAX_VAL, self.controller.K[3], "K_omega2 (Wahadlo vel)", step=0.1),
        ]

        self.btn_reset = Button(20, 180, 200, 24, "RESET DO GÓRY (SPACE)")

        self.MAX_HIST = 150
        self.hist_pend = deque(maxlen=self.MAX_HIST)
        self.hist_arm = deque(maxlen=self.MAX_HIST)
        self.hist_sp = deque(maxlen=self.MAX_HIST)
        self.hist_u = deque(maxlen=self.MAX_HIST)  # Bufor dla momentu sterującego

        self.update_status()

    def update_status(self):
        """Aktualizuje atrybuty statusu wewnętrznego."""
        self.status_text = f"LQR: {'AKTYWNY' if self.controller.active else 'UPADEK (SPACJA)'} | Arm: {math.degrees(self.physics.theta1):.1f}°"
        self.status_color = (80, 230, 120) if self.controller.active else (230, 80, 80)

    def reset_state(self):
        self.setpoint_arm = 0.0
        self.physics.reset()
        self.hist_pend.clear()
        self.hist_arm.clear()
        self.hist_sp.clear()
        self.hist_u.clear()  # Czyszczenie bufora sterowania
        self.update_status()

    def reset(self):
        self.reset_state()

    def set_target_from_input(self, norm_x, norm_y=0.5):
        self.setpoint_arm = normalize_angle((norm_x - 0.5) * math.pi * 2.0)

    def set_target_angle(self, angle_rad):
        self.setpoint_arm = normalize_angle(angle_rad)

    def process_serial_data(self, roll, pitch):
        self.setpoint_arm = normalize_angle(math.radians(roll))

    def step(self, dt):
        for i in range(4):
            self.controller.K[i] = self.sliders[i].val

        torque = self.controller.update(self.setpoint_arm)
        self.physics.step(torque, dt)

        self.hist_pend.append(math.degrees(self.physics.theta2))
        self.hist_arm.append(math.degrees(self.physics.theta1))
        self.hist_sp.append(math.degrees(self.setpoint_arm))
        self.hist_u.append(torque)  # Rejestracja sygnału sterującego

        self.update_status()

    def draw_3d(self):
        draw_furuta_3d(self.physics, self.setpoint_arm)

    def render_3d(self):
        self.draw_3d()

    def get_widgets(self):
        return self.sliders + [self.btn_reset]

    def get_charts_data(self):
        return {
            "arm_chart": [
                {"data": list(self.hist_sp), "color": (80, 220, 120)},
                {"data": list(self.hist_arm), "color": (255, 200, 80)},
            ],
            "pendulum_chart": [
                {"data": list(self.hist_pend), "color": (100, 200, 255)}
            ],
            "u_chart": [
                {"data": list(self.hist_u), "color": (255, 180, 80)}
            ]
        }