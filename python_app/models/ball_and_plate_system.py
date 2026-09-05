import math
import numpy as np
from collections import deque
from statistics import median
from models.base_system import BaseSystem
from ui.renderer_3d import draw_ball_and_plate_scene
from ui.widgets import Button, Slider


class BallAndPlateSystem(BaseSystem):
    def __init__(self, config):
        super().__init__()
        self.config = config

        # Pobieranie parametrów z konfiguracji
        params = getattr(config, "BALL_PLATE_PARAMS", {})
        self.plate_size = params.get("plate_size", 1.4)
        self.plate_thickness = params.get("plate_thickness", 0.05)
        self.ball_radius = params.get("ball_radius", 0.09)
        self.g = params.get("g", 9.81)
        self.damping = params.get("damping", 1.2)
        self.restitution = params.get("restitution", 0.4)

        pid_cfg = getattr(config, "PID_BALL_PLATE_CONFIG", {})
        self.Kp = pid_cfg.get("Kp_default", 3.5)
        self.Kd = pid_cfg.get("Kd_default", 2.8)

        # Wysokość zawieszenia platformy nad podłożem [m]
        self.elevation = 0.5

        # Stany układu
        self.ball_pos = [0.0, 0.0]  # x, y [m]
        self.ball_vel = [0.0, 0.0]  # vx, vy [m/s]
        self.setpoint_x = 0.0
        self.setpoint_y = 0.0

        # Kąty płytki [deg]
        self.plate_roll = 0.0
        self.plate_pitch = 0.0

        # FILTR MEDIANOWY dla odczytów z IMU
        self.roll_buffer = deque([0.0] * 5, maxlen=5)
        self.pitch_buffer = deque([0.0] * 5, maxlen=5)

        self.use_imu_as_setpoint = True
        self.imu_sensitivity = 25.0

        # ATRYBUTY STATUSU
        self.status_text = "BALL & PLATE ACTIVE"
        self.status_color = (0, 255, 100)

        # Kontroler PID (PD)
        class PID:
            def __init__(self, Kp, Kd):
                self.Kp = Kp
                self.Kd = Kd
                self.prev_error = 0.0

            def update(self, setpoint, current, dt):
                if dt <= 0.0001:
                    return 0.0
                error = setpoint - current
                derivative = (error - self.prev_error) / dt
                self.prev_error = error
                return self.Kp * error + self.Kd * derivative

        self.pid_x = PID(self.Kp, self.Kd)
        self.pid_y = PID(self.Kp, self.Kd)

        # WIDGETY UI
        self.slider_kp = Slider(20, 45, 220, 12, 0.0, 15.0, self.Kp, "Kp")
        self.slider_kd = Slider(20, 85, 220, 12, 0.0, 10.0, self.Kd, "Kd")
        self.btn_reset = Button(20, 115, 220, 25, "RESET STANU (SPACE)")

        # BUFORY HISTORII DLA WYKRESÓW
        self.MAX_HIST = 150
        self.hist_sp_x = deque(maxlen=self.MAX_HIST)
        self.hist_pv_x = deque(maxlen=self.MAX_HIST)
        self.hist_sp_y = deque(maxlen=self.MAX_HIST)
        self.hist_pv_y = deque(maxlen=self.MAX_HIST)
        self.hist_roll = deque(maxlen=self.MAX_HIST)
        self.hist_pitch = deque(maxlen=self.MAX_HIST)
        # Dodane bufory na sygnały sterujące U [deg]
        self.hist_u_pitch = deque(maxlen=self.MAX_HIST)
        self.hist_u_roll = deque(maxlen=self.MAX_HIST)

        self.reset_state()

    def update_params(self, Kp, Kd):
        self.Kp = Kp
        self.Kd = Kd
        self.pid_x.Kp = Kp
        self.pid_x.Kd = Kd
        self.pid_y.Kp = Kp
        self.pid_y.Kd = Kd

    def update_status(self):
        """Aktualizuje tekst statusu z położeniem kulki oraz informacją o trybie."""
        mode_str = "IMU TARGET" if self.use_imu_as_setpoint else "MANUAL / PID"
        self.status_text = f"BALL & PLATE ({mode_str}) | Pos: X={self.ball_pos[0]:.2f}m, Y={self.ball_pos[1]:.2f}m"
        self.status_color = (0, 255, 100)

    def reset_state(self):
        self.ball_pos = [0.0, 0.0]
        self.ball_vel = [0.0, 0.0]
        self.plate_roll = 0.0
        self.plate_pitch = 0.0
        self.setpoint_x = 0.0
        self.setpoint_y = 0.0
        self.pid_x.prev_error = 0.0
        self.pid_y.prev_error = 0.0
        self.roll_buffer.clear()
        self.pitch_buffer.clear()
        self.roll_buffer.extend([0.0] * 5)
        self.pitch_buffer.extend([0.0] * 5)

        self.hist_sp_x.clear()
        self.hist_pv_x.clear()
        self.hist_sp_y.clear()
        self.hist_pv_y.clear()
        self.hist_roll.clear()
        self.hist_pitch.clear()
        self.hist_u_pitch.clear()
        self.hist_u_roll.clear()

        # Inicjalizacja buforów zerami, aby uniknąć pustych serii na starcie
        self.hist_u_pitch.extend([0.0] * self.MAX_HIST)
        self.hist_u_roll.extend([0.0] * self.MAX_HIST)

        self.update_status()

    def reset(self):
        self.reset_state()

    def set_target_from_input(self, norm_x, norm_y=0.5):
        limit_pos = self.plate_size - self.ball_radius
        self.setpoint_x = (norm_x - 0.5) * (limit_pos * 2)
        self.setpoint_y = (norm_y - 0.5) * (limit_pos * 2)

    def get_widgets(self):
        return [self.slider_kp, self.slider_kd, self.btn_reset]

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
            "angles_chart": [
                {"data": list(self.hist_roll), "color": (255, 90, 90)},
                {"data": list(self.hist_pitch), "color": (180, 130, 255)},
            ],
            # Zwracanie danych sterowania dla panelu GUI
            "u_chart": [
                {"data": list(self.hist_u_pitch), "color": (255, 140, 0)},
                {"data": list(self.hist_u_roll), "color": (0, 220, 220)},
            ],
        }

    def process_serial_data(self, roll, pitch):
        self.roll_buffer.append(roll)
        self.pitch_buffer.append(pitch)

        filtered_roll = median(self.roll_buffer)
        filtered_pitch = median(self.pitch_buffer)

        if self.use_imu_as_setpoint:
            max_pos = self.plate_size - self.ball_radius
            self.setpoint_x = max(-max_pos, min(max_pos, (filtered_roll / self.imu_sensitivity) * max_pos))
            self.setpoint_y = max(-max_pos, min(max_pos, (filtered_pitch / self.imu_sensitivity) * max_pos))
        else:
            self.plate_roll = max(-20.0, min(20.0, filtered_roll))
            self.plate_pitch = max(-20.0, min(20.0, filtered_pitch))

    def step(self, dt):
        # Synchronizacja parametrów regulatora z wartościami ze suwaków
        self.update_params(self.slider_kp.val, self.slider_kd.val)

        if dt <= 0.0001:
            return self.plate_roll, self.plate_pitch

        # 1. PĘTLA REGULATORA PID
        if self.use_imu_as_setpoint:
            target_pitch = -self.pid_x.update(self.setpoint_x, self.ball_pos[0], dt)
            target_roll = self.pid_y.update(self.setpoint_y, self.ball_pos[1], dt)

            # Zapisanie niewycętych/surowych sygnałów sterujących lub z ograniczeniem
            u_pitch = max(-18.0, min(18.0, target_pitch))
            u_roll = max(-18.0, min(18.0, target_roll))

            self.plate_pitch = u_pitch
            self.plate_roll = u_roll
        else:
            u_pitch = self.plate_pitch
            u_roll = self.plate_roll

        # Zapis do historii sterowań
        self.hist_u_pitch.append(u_pitch)
        self.hist_u_roll.append(u_roll)

        # 2. FIZYKA KULKI
        rad_pitch = math.radians(self.plate_pitch)
        rad_roll = math.radians(self.plate_roll)

        ax = -(5.0 / 7.0) * self.g * math.sin(rad_pitch) - self.damping * self.ball_vel[0]
        ay = (5.0 / 7.0) * self.g * math.sin(rad_roll) - self.damping * self.ball_vel[1]

        self.ball_vel[0] += ax * dt
        self.ball_vel[1] += ay * dt
        self.ball_pos[0] += self.ball_vel[0] * dt
        self.ball_pos[1] += self.ball_vel[1] * dt

        limit = self.plate_size - self.ball_radius
        for i in range(2):
            if abs(self.ball_pos[i]) > limit:
                self.ball_pos[i] = math.copysign(limit, self.ball_pos[i])
                self.ball_vel[i] = -self.ball_vel[i] * self.restitution

        # 3. AKTUALIZACJA HISTORII DLA WYKRESÓW STANÓW
        self.hist_sp_x.append(self.setpoint_x)
        self.hist_pv_x.append(self.ball_pos[0])
        self.hist_sp_y.append(self.setpoint_y)
        self.hist_pv_y.append(self.ball_pos[1])
        self.hist_roll.append(self.plate_roll)
        self.hist_pitch.append(self.plate_pitch)

        # 4. AKTUALIZACJA STATUSU
        self.update_status()

        return self.plate_roll, self.plate_pitch

    def draw_3d(self):
        draw_ball_and_plate_scene(self)

    def render_3d(self):
        self.draw_3d()