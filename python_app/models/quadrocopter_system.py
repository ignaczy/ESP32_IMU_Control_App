import math
from collections import deque
from statistics import median
from OpenGL.GL import *
from OpenGL.GLU import *
from models.base_system import BaseSystem

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
        
        self.arm_len = getattr(config, 'QUAD_ARM_LEN', 0.25)
        self.g = 9.81
        
        self.median_filter = MedianFilter(window_size=getattr(config, 'QUAD_FILTER_WINDOW', 5))
        
        self.pid_x = SafePID(
            Kp=getattr(config, 'QUAD_KP_DEFAULT', 2.5),
            Ki=getattr(config, 'QUAD_KI_DEFAULT', 0.0),
            Kd=getattr(config, 'QUAD_KD_DEFAULT', 2.0),
            limit=getattr(config, 'QUAD_PID_LIMIT', 15.0)
        )
        self.pid_y = SafePID(
            Kp=getattr(config, 'QUAD_KP_DEFAULT', 2.5),
            Ki=getattr(config, 'QUAD_KI_DEFAULT', 0.0),
            Kd=getattr(config, 'QUAD_KD_DEFAULT', 2.0),
            limit=getattr(config, 'QUAD_PID_LIMIT', 15.0)
        )
        
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

    def render_3d(self):
        # --- 1. Rysowanie celu (Target point) ---
        glDisable(GL_LIGHTING)
        glColor4f(0.2, 0.9, 0.4, 0.4)
        glLineWidth(1.5)
        glBegin(GL_LINES)
        glVertex3f(self.setpoint_x, self.setpoint_y, 0.0)
        glVertex3f(self.setpoint_x, self.setpoint_y, 0.8)
        glEnd()

        glPointSize(10.0)
        glBegin(GL_POINTS)
        glColor3f(0.2, 0.95, 0.4)
        glVertex3f(self.setpoint_x, self.setpoint_y, 0.8)
        glEnd()
        glEnable(GL_LIGHTING)

        # --- 2. Rysowanie Quadrocoptera ---
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        
        # Orientacja 3D
        if hasattr(self, 'attitude'):
            glRotatef(math.degrees(self.attitude[2]), 0, 0, 1)  # Yaw
            glRotatef(math.degrees(self.attitude[1]), 0, 1, 0)  # Pitch
            glRotatef(math.degrees(self.attitude[0]), 1, 0, 0)  # Roll
        else:
            glRotatef(math.degrees(getattr(self, 'theta', 0.0)), 1, 0, 0)
            glRotatef(math.degrees(getattr(self, 'phi', 0.0)), 0, 1, 0)

        # A. Korpus główny (Bardzo jasny, jaskrawy pomarańcz)
        glPushMatrix()
        glScalef(0.08, 0.08, 0.01)
        glColor3f(1.0, 0.5, 0.0)
        glBegin(GL_QUADS)
        for dx, dy, dz in [(0,0,1), (0,0,-1), (0,1,0), (0,-1,0), (1,0,0), (-1,0,0)]:
            glNormal3f(float(dx), float(dy), float(dz))
            glVertex3f(-1, -1, dz); glVertex3f(1, -1, dz)
            glVertex3f(1, 1, dz); glVertex3f(-1, 1, dz)
        glEnd()
        glPopMatrix()

        # B. Centralny akcent na płytce (Jaskrawa, neonowa żółć)
        glPushMatrix()
        glTranslatef(0, 0, 0.0105)
        glScalef(0.04, 0.04, 0.003)
        glColor3f(1.0, 1.0, 0.2)
        glBegin(GL_QUADS)
        for dx, dy, dz in [(0,0,1), (0,0,-1), (0,1,0), (0,-1,0), (1,0,0), (-1,0,0)]:
            glNormal3f(float(dx), float(dy), float(dz))
            glVertex3f(-1, -1, dz); glVertex3f(1, -1, dz)
            glVertex3f(1, 1, dz); glVertex3f(-1, 1, dz)
        glEnd()
        glPopMatrix()

        # C. Akumulator (Czysty, jasny biały)
        glPushMatrix()
        glTranslatef(0, 0, -0.018)
        glScalef(0.045, 0.065, 0.01)
        glColor3f(0.95, 0.95, 0.95)
        glBegin(GL_QUADS)
        for dx, dy, dz in [(0,0,1), (0,0,-1), (0,1,0), (0,-1,0), (1,0,0), (-1,0,0)]:
            glNormal3f(float(dx), float(dy), float(dz))
            glVertex3f(-1, -1, dz); glVertex3f(1, -1, dz)
            glVertex3f(1, 1, dz); glVertex3f(-1, 1, dz)
        glEnd()
        glPopMatrix()

        # D. Ramiona, Silniki i Śmigła
        arm = getattr(self, 'arm_len', 0.25) * 0.75
        rotors = [
            (-arm, -arm, False),  # Tył-Lewo
            (arm, -arm, False),   # Tył-Prawo
            (-arm, arm, True),    # Przód-Lewo
            (arm, arm, True)      # Przód-Prawo
        ]

        prop_rot = getattr(self, 'prop_angle', 0.0)

        for rx, ry, is_front in rotors:
            # Belki ramion (Jasny pomarańcz z przodu, szaro-biały z tyłu)
            glPushMatrix()
            if is_front:
                glColor3f(1.0, 0.55, 0.0)  # Jasny Pomarańcz
            else:
                glColor3f(0.85, 0.85, 0.9)  # Jasnoszary / Biały
                
            glLineWidth(7)
            glBegin(GL_LINES)
            glNormal3f(0, 0, 1)
            glVertex3f(0, 0, 0)
            glVertex3f(rx, ry, 0)
            glEnd()
            glPopMatrix()

            # Obudowa silnika
            glPushMatrix()
            glTranslatef(rx, ry, -0.025)
            
            # Silnik (Srebrny/Lśniący)
            glColor3f(0.9, 0.9, 0.95)
            self._draw_cylinder(0.015, 0.04)

            # Mocowanie silnika (Ciemny kontrastowy detal)
            glColor3f(0.2, 0.2, 0.2)
            self._draw_cylinder(0.018, 0.015)

            # Śmigła (Jaskrawa żółć)
            glTranslatef(0, 0, 0.042)
            glRotatef(prop_rot if not is_front else -prop_rot, 0, 0, 1)
            
            glColor3f(1.0, 0.9, 0.0)
            glLineWidth(4)
            glBegin(GL_LINES)
            glNormal3f(0, 0, 1)
            glVertex3f(-0.09, 0, 0)
            glVertex3f(0.09, 0, 0)
            glEnd()
            glPopMatrix()

        glPopMatrix()
    
    def _draw_cylinder(self, radius, height, slices=16):
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        gluCylinder(quadric, radius, radius, height, slices, 1)
        gluDeleteQuadric(quadric)
        
        
    # nowe dodane    
    def draw_3d(self):
        """Wymagana przez interfejs metoda do rysowania obiektu w OpenGL."""
        # Jeśli masz już zaimplementowaną metodę render_3d, wystarczy ją wywołać:
        self.render_3d()

    def reset(self):
        """Wymagana przez interfejs metoda do resetowania stanu."""
        # Jeśli używasz reset_state(), wywołaj ją w tej metodzie:
        if hasattr(self, 'reset_state'):
            self.reset_state()

    def set_target_from_input(self, norm_x):
        """Ustawia cel na podstawie kliknięcia na ekranie (norm_x w zakresie 0..1)."""
        self.setpoint_x = (norm_x - 0.5) * 4.0

    def get_widgets(self):
        """Zwraca listę widgetów GUI powiązanych z tym systemem."""
        # Zwróć pustą listę lub listę suwaków/przycisków związanych z dronem
        return []

    def get_charts_data(self):
        """Zwraca dane do wykresów w formacie oczekiwanym przez interfejs."""
        return {
            "pendulum_chart": [],
            "arm_chart": [],
            "status_text": f"Pos: X={self.pos[0]:.2f}m, Y={self.pos[1]:.2f}m",
            "status_color": (0, 255, 100)
        }