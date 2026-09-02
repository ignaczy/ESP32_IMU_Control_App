import math
import numpy as np
from collections import deque
from statistics import median
from OpenGL.GL import *
from OpenGL.GLU import *

class BallAndPlateSystem:
    def __init__(self, config):
        self.config = config
        
        # Pobieranie parametrów z konfiguracji
        params = getattr(config, 'BALL_PLATE_PARAMS', {})
        self.plate_size = params.get('plate_size', 1.4)
        self.plate_thickness = params.get('plate_thickness', 0.05)
        self.ball_radius = params.get('ball_radius', 0.09)
        self.g = params.get('g', 9.81)
        self.damping = params.get('damping', 1.2)
        self.restitution = params.get('restitution', 0.4)

        pid_cfg = getattr(config, 'PID_BALL_PLATE_CONFIG', {})
        self.Kp = pid_cfg.get('Kp_default', 3.5)
        self.Kd = pid_cfg.get('Kd_default', 2.8)

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

        # FILTR MEDIANOWY dla odczytów z IMU (okno 5 próbek)
        self.roll_buffer = deque([0.0] * 5, maxlen=5)
        self.pitch_buffer = deque([0.0] * 5, maxlen=5)

        # Tryb sterowania: 
        # True  -> IMU steruje pozycją celu (Setpoint), PID pilnuje kulki
        # False -> IMU bezpośrednio przechyla płytkę
        self.use_imu_as_setpoint = True
        self.imu_sensitivity = 25.0

        # Kontroler PID (Prosty PD dla X i Y)
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

    def update_params(self, Kp, Kd):
        self.Kp = Kp
        self.Kd = Kd
        self.pid_x.Kp = Kp
        self.pid_x.Kd = Kd
        self.pid_y.Kp = Kp
        self.pid_y.Kd = Kd

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

    def reset(self):
        """Wymagane przez klasę bazową"""
        self.reset_state()

    def set_target_from_input(self, norm_x, norm_y=0.5):
        """Przeliczanie pozycji z interfejsu na cel w metrach"""
        limit_pos = self.plate_size - self.ball_radius
        self.setpoint_x = (norm_x - 0.5) * (limit_pos * 2)
        self.setpoint_y = (norm_y - 0.5) * (limit_pos * 2)

    def get_widgets(self):
        return []

    def get_charts_data(self):
        return {
            "pendulum_chart": [
                {"data": [self.setpoint_x], "color": (80, 220, 120)},
                {"data": [self.ball_pos[0]], "color": (100, 200, 255)}
            ],
            "arm_chart": [
                {"data": [self.setpoint_y], "color": (80, 220, 120)},
                {"data": [self.ball_pos[1]], "color": (200, 100, 255)}
            ],
            "status_text": "BALL & PLATE ACTIVE",
            "status_color": (0, 255, 100)
        }

    def process_serial_data(self, roll, pitch):
        """Obsługa odczytów z IMU z użyciem filtru medianowego"""
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
        """Krok symulacji fizycznej i pętli sterowania"""
        if dt <= 0.0001:
            return self.plate_roll, self.plate_pitch

        # 1. PĘTLA REGULATORA PID
        if self.use_imu_as_setpoint:
            target_pitch = -self.pid_x.update(self.setpoint_x, self.ball_pos[0], dt)
            target_roll = self.pid_y.update(self.setpoint_y, self.ball_pos[1], dt)

            self.plate_pitch = max(-18.0, min(18.0, target_pitch))
            self.plate_roll = max(-18.0, min(18.0, target_roll))

        # 2. FIZYKA KULKI (Staczanie po pochyłości)
        rad_pitch = math.radians(self.plate_pitch)
        rad_roll = math.radians(self.plate_roll)

        ax = -(5.0 / 7.0) * self.g * math.sin(rad_pitch) - self.damping * self.ball_vel[0]
        ay = (5.0 / 7.0) * self.g * math.sin(rad_roll) - self.damping * self.ball_vel[1]

        # Całkowanie stanu fizycznego
        self.ball_vel[0] += ax * dt
        self.ball_vel[1] += ay * dt
        self.ball_pos[0] += self.ball_vel[0] * dt
        self.ball_pos[1] += self.ball_vel[1] * dt

        # Ograniczenia i odbicia od krawędzi płytki
        limit = self.plate_size - self.ball_radius
        for i in range(2):
            if abs(self.ball_pos[i]) > limit:
                self.ball_pos[i] = math.copysign(limit, self.ball_pos[i])
                self.ball_vel[i] = -self.ball_vel[i] * self.restitution

        return self.plate_roll, self.plate_pitch

    def render_3d(self):
        self.draw_3d()

    def draw_3d(self):
        glPushMatrix()
        
        # UNIESIENIE PLATFORMY NAD PODŁOŻE
        glTranslatef(0.0, 0.0, self.elevation)

        # ODKSZTAŁCENIE / NACHYLENIE PLATFORMY W OPENGL
        glRotatef(-self.plate_pitch, 0.0, 1.0, 0.0)
        glRotatef(-self.plate_roll, 1.0, 0.0, 0.0)

        hx = hy = self.plate_size
        hz = self.plate_thickness / 2.0

        # 1. Rysowanie płytki - Ciemnoniebieskie wypełnienie
        glColor3f(0.08, 0.15, 0.25)
        glBegin(GL_QUADS)
        # Górna powierzchnia
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(-hx, -hy, hz); glVertex3f(hx, -hy, hz); glVertex3f(hx, hy, hz); glVertex3f(-hx, hy, hz)
        # Dolna powierzchnia
        glNormal3f(0.0, 0.0, -1.0)
        glVertex3f(-hx, -hy, -hz); glVertex3f(-hx, hy, -hz); glVertex3f(hx, hy, -hz); glVertex3f(hx, -hy, -hz)
        # Boki
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-hx, hy, -hz); glVertex3f(-hx, hy, hz); glVertex3f(hx, hy, hz); glVertex3f(hx, hy, -hz)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(-hx, -hy, -hz); glVertex3f(hx, -hy, -hz); glVertex3f(hx, -hy, hz); glVertex3f(-hx, -hy, hz)
        glNormal3f(1.0, 0.0, 0.0)
        glVertex3f(hx, -hy, -hz); glVertex3f(hx, hy, -hz); glVertex3f(hx, hy, hz); glVertex3f(hx, -hy, hz)
        glNormal3f(-1.0, 0.0, 0.0)
        glVertex3f(-hx, -hy, -hz); glVertex3f(-hx, -hy, hz); glVertex3f(-hx, hy, hz); glVertex3f(-hx, hy, -hz)
        glEnd()

        # Obramowanie płytki - Jasnoszary / Srebrny brzeg
        glLineWidth(3.0)
        glColor3f(0.7, 0.8, 0.9)
        glBegin(GL_LINE_LOOP)
        glVertex3f(-hx, -hy, hz + 0.001)
        glVertex3f(hx, -hy, hz + 0.001)
        glVertex3f(hx, hy, hz + 0.001)
        glVertex3f(-hx, hy, hz + 0.001)
        glEnd()

        # 2. Cel (Setpoint) - Zielony pierścień / Okrąg
        glPushMatrix()
        glTranslatef(self.setpoint_x, self.setpoint_y, hz + 0.002)
        glColor3f(0.0, 1.0, 0.4)
        glLineWidth(3.5)
        
        segments = 32
        radius = 0.08
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            rx = radius * math.cos(angle)
            ry = radius * math.sin(angle)
            glVertex3f(rx, ry, 0.0)
        glEnd()
        glPopMatrix()

        # 3. Kula (Ball) - Czerwona sfera na powierzchni
        glPushMatrix()
        glTranslatef(self.ball_pos[0], self.ball_pos[1], hz + self.ball_radius)
        glColor3f(0.95, 0.2, 0.2)
        quad_ball = gluNewQuadric()
        gluQuadricNormals(quad_ball, GLU_SMOOTH)
        gluSphere(quad_ball, self.ball_radius, 24, 24)
        gluDeleteQuadric(quad_ball)
        glPopMatrix()

        glPopMatrix()