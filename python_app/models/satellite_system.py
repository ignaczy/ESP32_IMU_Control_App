import math
import random
from collections import deque
from OpenGL.GL import *
from OpenGL.GLU import *


def angle_difference(target, current):
    return (target - current + math.pi) % (2 * math.pi) - math.pi


def normalize_angle(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi


# --- MATERIAŁY I GEOMETRIA Z ORYGINALNEGO KODU ---
def apply_material(diffuse, specular=[0.0, 0.0, 0.0, 1.0], shininess=0.0):
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, diffuse)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, specular)
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shininess)


def draw_box(dx, dy, dz):
    hx, hy, hz = dx / 2.0, dy / 2.0, dz / 2.0
    faces = [
        ((0, 0, 1),  [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]),
        ((0, 0, -1), [(-hx, hy, -hz), (hx, hy, -hz), (hx, -hy, -hz), (-hx, -hy, -hz)]),
        ((0, 1, 0),  [(-hx, hy, -hz), (-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz)]),
        ((0, -1, 0), [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)]),
        ((1, 0, 0),  [(hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz), (hx, -hy, hz)]),
        ((-1, 0, 0), [(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)])
    ]
    glBegin(GL_QUADS)
    for normal, vertices in faces:
        glNormal3f(*normal)
        for v in vertices:
            glVertex3f(*v)
    glEnd()


STARS = [(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-8, -2)) for _ in range(150)]


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


class SatelliteSystem:
    def __init__(self):
        # Parametry fizyczne z oryginalnego kodu
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

    def set_target_from_input(self, norm_x):
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
        self.draw_3d()

    def draw_3d(self):
        # Resetowanie stanu OpenGL przed rysowaniem
        glDisable(GL_COLOR_MATERIAL)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glShadeModel(GL_SMOOTH)

        glLightfv(GL_LIGHT0, GL_POSITION, [3.0, 4.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.98, 0.9, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.22, 0.3, 1.0])

        self._draw_space_background()
        self._draw_target_indicator(self.setpoint_angle)
        self._draw_satellite_3d()

    def _draw_space_background(self):
        glDisable(GL_LIGHTING)
        glPointSize(1.5)
        glBegin(GL_POINTS)
        glColor3f(0.8, 0.8, 1.0)
        for st in STARS:
            glVertex3f(*st)
        glEnd()

        glLineWidth(1)
        glBegin(GL_LINES)
        glColor3f(0.12, 0.15, 0.22)
        for r in [1.5, 2.5, 3.5]:
            for i in range(36):
                a1 = 2 * math.pi * i / 36
                a2 = 2 * math.pi * (i + 1) / 36
                glVertex3f(r * math.cos(a1), r * math.sin(a1), -0.5)
                glVertex3f(r * math.cos(a2), r * math.sin(a2), -0.5)
        glEnd()
        glEnable(GL_LIGHTING)

    def _draw_target_indicator(self, angle):
        glPushMatrix()
        glRotatef(math.degrees(angle), 0, 0, 1)
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.8, 0.2)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(2.0, 0.0, 0.0)
        glEnd()

        glBegin(GL_TRIANGLES)
        glVertex3f(2.0, 0.0, 0.0)
        glVertex3f(1.8, 0.08, 0.0)
        glVertex3f(1.8, -0.08, 0.0)
        glEnd()
        glEnable(GL_LIGHTING)
        glPopMatrix()

    def _draw_solar_panel(self):
        # Podstawa panelu
        apply_material([0.15, 0.15, 0.18, 1.0], [0.5, 0.5, 0.5, 1.0], 20.0)
        draw_box(1.4, 0.65, 0.04)

        # Siatka ogniw słonecznych (ciemnoniebieskie)
        apply_material([0.02, 0.08, 0.35, 1.0], [0.6, 0.7, 1.0, 1.0], 80.0)
        glPushMatrix()
        glTranslatef(0, 0, 0.025)
        for row in [-0.2, 0.2]:
            for col in [-0.5, -0.2, 0.1, 0.4]:
                glPushMatrix()
                glTranslatef(col, row, 0)
                draw_box(0.26, 0.22, 0.005)
                glPopMatrix()
        glPopMatrix()

    def _draw_satellite_3d(self):
        glPushMatrix()
        glRotatef(math.degrees(self.angle_sat), 0, 0, 1)

        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)

        # 1. Główny korpus (Antracytowy / Tytanowy)
        apply_material([0.25, 0.27, 0.3, 1.0], [0.8, 0.8, 0.9, 1.0], 50.0)
        draw_box(0.9, 0.9, 0.5)

        # 2. Złota osłona termiczna (MLI) pośrodku
        apply_material([0.9, 0.7, 0.1, 1.0], [1.0, 0.9, 0.4, 1.0], 90.0)
        draw_box(0.92, 0.4, 0.52)

        # 3. Panele Słoneczne (Lewy i Prawy)
        glPushMatrix()
        glTranslatef(-1.25, 0, 0)
        self._draw_solar_panel()
        glPopMatrix()

        glPushMatrix()
        glTranslatef(1.25, 0, 0)
        self._draw_solar_panel()
        glPopMatrix()

        # 4. Wysięgniki paneli słonecznych
        apply_material([0.6, 0.6, 0.65, 1.0], [0.9, 0.9, 0.9, 1.0], 30.0)
        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * 0.5, 0, 0)
            glRotatef(90, 0, 1, 0)
            gluCylinder(quad, 0.025, 0.025, 0.1, 12, 1)
            glPopMatrix()

        # 5. Przód Satelity (Kamera / Sensor optyczny)
        glPushMatrix()
        glTranslatef(0.46, 0.0, 0.0)
        apply_material([0.8, 0.1, 0.1, 1.0], [1.0, 0.5, 0.5, 1.0], 60.0)
        draw_box(0.04, 0.35, 0.35)

        glTranslatef(0.02, 0, 0)
        glRotatef(90, 0, 1, 0)
        apply_material([0.1, 0.1, 0.1, 1.0], [0.9, 0.9, 1.0, 1.0], 100.0)
        gluCylinder(quad, 0.1, 0.08, 0.08, 16, 1)
        gluDisk(quad, 0, 0.1, 16, 1)
        glPopMatrix()

        # 6. Tył Satelity - Antena paraboliczna
        glPushMatrix()
        glTranslatef(-0.46, 0, 0)
        glRotatef(-90, 0, 1, 0)
        apply_material([0.85, 0.85, 0.85, 1.0], [1.0, 1.0, 1.0, 1.0], 40.0)
        gluCylinder(quad, 0.02, 0.18, 0.12, 16, 1)
        glPopMatrix()

        # 7. Koło Reakcyjne
        glPushMatrix()
        glTranslatef(0, 0, 0.25)

        # Ciemna podstawa montażowa (Stojan silnika)
        apply_material([0.12, 0.14, 0.18, 1.0], [0.3, 0.3, 0.3, 1.0], 10.0)
        gluCylinder(quad, 0.38, 0.38, 0.04, 32, 1)

        # Przejście do wirnika
        glTranslatef(0, 0, 0.04)
        glRotatef(math.degrees(self.angle_wheel), 0, 0, 1)

        # Wewnętrzna piasta stalowa
        apply_material([0.3, 0.32, 0.38, 1.0], [0.8, 0.8, 0.9, 1.0], 60.0)
        gluCylinder(quad, 0.12, 0.12, 0.08, 24, 1)
        gluDisk(quad, 0, 0.12, 24, 1)

        # Mosiężny/Złoty pierścień masy bezwładnościowej
        apply_material([0.85, 0.65, 0.15, 1.0], [1.0, 0.85, 0.4, 1.0], 80.0)
        gluCylinder(quad, 0.36, 0.36, 0.08, 32, 1)
        gluDisk(quad, 0.26, 0.36, 32, 1)

        # 4 Ramiona łączące piastę z wieńcem
        apply_material([0.2, 0.22, 0.25, 1.0], [0.5, 0.5, 0.5, 1.0], 30.0)
        for i in range(4):
            glPushMatrix()
            glRotatef(i * 90, 0, 0, 1)
            glTranslatef(0.19, 0, 0.04)
            draw_box(0.16, 0.04, 0.03)
            glPopMatrix()

        # Wskaźnik obrotu
        glDisable(GL_LIGHTING)
        glColor3f(0.1, 1.0, 0.4)
        glLineWidth(4)
        glBegin(GL_LINES)
        glVertex3f(-0.34, 0.0, 0.085)
        glVertex3f(0.34, 0.0, 0.085)
        glEnd()

        glPointSize(6.0)
        glBegin(GL_POINTS)
        glVertex3f(0.0, -0.31, 0.085)
        glVertex3f(0.0, 0.31, 0.085)
        glEnd()
        glEnable(GL_LIGHTING)

        glPopMatrix()

        gluDeleteQuadric(quad)
        glPopMatrix()