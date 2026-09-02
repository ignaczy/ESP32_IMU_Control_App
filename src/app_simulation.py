import sys
import math
import serial
import pygame
import random
from collections import deque
from statistics import median
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

# --- KONFIGURACJA PORTU SERIAL ---
SERIAL_PORT = 'COM8'
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.01)
    print(f"Połączono z {SERIAL_PORT}")
except Exception as e:
    print(f"Brak portu {SERIAL_PORT} (Tryb myszki/klawiatury): {e}")
    ser = None

def angle_difference(target, current):
    return (target - current + math.pi) % (2 * math.pi) - math.pi

def normalize_angle(angle):
    return (angle + math.pi) % (2 * math.pi) - math.pi

# --- REGULATOR PID ---
class SatellitePID:
    def __init__(self, Kp, Ki, Kd, max_torque=25.0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.max_torque = max_torque
        self.reset()

    def reset(self):
        self.integral = 0.0

    def update(self, setpoint_angle, sat_angle, sat_omega, dt):
        if dt <= 0.0001:
            return 0.0

        error = angle_difference(setpoint_angle, sat_angle)
        self.integral += error * dt
        self.integral = max(-5.0, min(5.0, self.integral))

        output = (self.Kp * error) + (self.Ki * self.integral) - (self.Kd * sat_omega)
        return max(-self.max_torque, min(self.max_torque, output))

# --- MODEL FIZYCZNY SATELITY ---
class ReactionWheelSatellite:
    def __init__(self):
        self.I_sat = 2.5        # Moment bezwładności kadłuba [kg*m^2]
        self.I_wheel = 0.3      # Moment bezwładności koła zamachowego [kg*m^2]
        self.max_wheel_speed = 300.0  # Limit prędkości obrotowej koła [rad/s]
        self.reset_state()

    def reset_state(self):
        self.angle_sat = 0.0
        self.omega_sat = 0.0
        self.angle_wheel = 0.0
        self.omega_wheel = 0.0

    def step(self, torque, dt):
        if dt <= 0.0001: 
            return

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

# --- UI ELEMENTS ---
class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, initial_val, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = initial_val
        self.label = label
        self.dragging = False

    def draw(self, surface, font):
        pygame.draw.rect(surface, (35, 40, 55), self.rect, border_radius=4)
        handle_x = self.rect.x + int((self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.w)
        handle_rect = pygame.Rect(handle_x - 6, self.rect.y - 3, 12, self.rect.h + 6)
        pygame.draw.rect(surface, (80, 190, 255), handle_rect, border_radius=4)

        txt = font.render(f"{self.label}: {self.val:.2f}", True, (230, 235, 245))
        surface.blit(txt, (self.rect.x, self.rect.y - 18))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == MOUSEMOTION and self.dragging:
            rel_x = max(0, min(event.pos[0] - self.rect.x, self.rect.w))
            self.val = self.min_val + (rel_x / self.rect.w) * (self.max_val - self.min_val)

class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.is_hovered = False

    def draw(self, surface, font):
        color = (200, 60, 60) if self.is_hovered else (150, 45, 45)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (230, 90, 90), self.rect, width=1, border_radius=6)
        txt = font.render(self.text, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            return True
        return False

def draw_chart(surface, rect, font, title, y_min, y_max, data_series):
    pygame.draw.rect(surface, (20, 23, 32), rect, border_radius=6)
    pygame.draw.rect(surface, (55, 60, 75), rect, width=1, border_radius=6)

    title_txt = font.render(title, True, (220, 225, 235))
    surface.blit(title_txt, (rect.x + 8, rect.y + 4))

    ax_x = rect.x + 40
    ax_y = rect.y + 22
    ax_w = rect.w - 50
    ax_h = rect.h - 30

    for i in range(3):
        gy = ax_y + ax_h * (i / 2.0)
        val = y_max - (i / 2.0) * (y_max - y_min)
        pygame.draw.line(surface, (38, 42, 52), (ax_x, gy), (ax_x + ax_w, gy), 1)
        lbl = font.render(f"{val:>4.1f}", True, (130, 135, 150))
        surface.blit(lbl, (rect.x + 2, gy - 6))

    pygame.draw.rect(surface, (65, 70, 85), (ax_x, ax_y, ax_w, ax_h), 1)

    for series in data_series:
        data = series["data"]
        color = series["color"]
        if len(data) > 1:
            pts = []
            max_samples = len(data)
            for i, val in enumerate(data):
                px = ax_x + i * (ax_w / (max_samples - 1 if max_samples > 1 else 1))
                clamped_val = max(y_min, min(y_max, val))
                norm_val = (clamped_val - y_min) / (y_max - y_min)
                py = ax_y + ax_h * (1.0 - norm_val)
                pts.append((px, py))
            pygame.draw.aalines(surface, color, False, pts)

# --- GEOMETRIA OPENGL ---
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

def draw_space_background():
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

def draw_solar_panel():
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

def draw_satellite_3d(sat):
    glPushMatrix()
    glRotatef(math.degrees(sat.angle_sat), 0, 0, 1)

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
    draw_solar_panel()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(1.25, 0, 0)
    draw_solar_panel()
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

    # =========================================================
    # 7. NOWE, UPĘKSZONE I WCIĄŻ BARDZO WIDOCZNE KOŁO REAKCYJNE
    # =========================================================
    glPushMatrix()
    glTranslatef(0, 0, 0.25)

    # Ciemna podstawa montażowa (Stojan silnika)
    apply_material([0.12, 0.14, 0.18, 1.0], [0.3, 0.3, 0.3, 1.0], 10.0)
    gluCylinder(quad, 0.38, 0.38, 0.04, 32, 1)
    
    # Przejście do wirnika
    glTranslatef(0, 0, 0.04)
    glRotatef(math.degrees(sat.angle_wheel), 0, 0, 1)

    # Wewnętrzna piasta stalowa
    apply_material([0.3, 0.32, 0.38, 1.0], [0.8, 0.8, 0.9, 1.0], 60.0)
    gluCylinder(quad, 0.12, 0.12, 0.08, 24, 1)
    gluDisk(quad, 0, 0.12, 24, 1)

    # Mosiężny/Złoty pierścień masy bezwładnościowej (zewnętrzny wieńca)
    apply_material([0.85, 0.65, 0.15, 1.0], [1.0, 0.85, 0.4, 1.0], 80.0)
    gluCylinder(quad, 0.36, 0.36, 0.08, 32, 1)
    gluDisk(quad, 0.26, 0.36, 32, 1)

    # 4 Ramiona łączące piastę z wieńcem (ażurowa struktura)
    apply_material([0.2, 0.22, 0.25, 1.0], [0.5, 0.5, 0.5, 1.0], 30.0)
    for i in range(4):
        glPushMatrix()
        glRotatef(i * 90, 0, 0, 1)
        glTranslatef(0.19, 0, 0.04)
        draw_box(0.16, 0.04, 0.03)
        glPopMatrix()

    # Wskaźnik obrotu (Kontrastowy zielony pasek + kropki na ramionach)
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

    glPopMatrix() # Koniec koła reakcyjnego

    gluDeleteQuadric(quad)
    glPopMatrix()
    
def draw_target_indicator(angle):
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

# --- MAIN ---
pygame.init()
pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)

WIDTH, HEIGHT = 1350, 750
VIEW3D_W = 980
PANEL_W = WIDTH - VIEW3D_W

screen = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
pygame.display.set_caption("Reaction Wheel Satellite 3D - Symulator Orientacji PID")

gui_surface = pygame.Surface((PANEL_W, HEIGHT))
font_small = pygame.font.SysFont("Arial", 11)
font_bold = pygame.font.SysFont("Arial", 12, bold=True)

gui_texture = glGenTextures(1)

satellite = ReactionWheelSatellite()
pid = SatellitePID(Kp=10.0, Ki=0.0, Kd=12.0, max_torque=25.0)

slider_kp = Slider(20, 35, 220, 12, 0.0, 30.0, pid.Kp, "Kp")
slider_kd = Slider(20, 75, 220, 12, 0.0, 30.0, pid.Kd, "Kd (Tłumienie)")
btn_reset = Button(20, 105, 220, 26, "RESET STANU SATELITY")

setpoint_angle = 0.0
roll_buffer = deque([0.0] * 5, maxlen=5)

hist_sp, hist_pv = [], []
hist_wheel_speed = []
MAX_HIST = 150

def reset_simulation():
    global setpoint_angle
    setpoint_angle = 0.0
    satellite.reset_state()
    pid.reset()

clock = pygame.time.Clock()
last_ticks = pygame.time.get_ticks()

running = True
while running:
    current_ticks = pygame.time.get_ticks()
    dt = (current_ticks - last_ticks) / 1000.0
    last_ticks = current_ticks
    if dt > 0.05: dt = 0.016

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

        if event.type == KEYDOWN and event.key == K_SPACE:
            reset_simulation()

        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            if event.pos[0] < VIEW3D_W:
                mx, my = event.pos
                dx = mx - (VIEW3D_W / 2.0)
                dy = (HEIGHT / 2.0) - my
                setpoint_angle = normalize_angle(math.atan2(dy, dx))

        if event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION):
            if event.pos[0] >= VIEW3D_W:
                event_panel = pygame.event.Event(event.type, event.__dict__)
                event_panel.pos = (event.pos[0] - VIEW3D_W, event.pos[1])
                slider_kp.handle_event(event_panel)
                slider_kd.handle_event(event_panel)
                if btn_reset.handle_event(event_panel):
                    reset_simulation()

    pid.Kp = slider_kp.val
    pid.Kd = slider_kd.val

    # Odczyt danych z MPU6050 przez port szeregowy
    if ser is not None and ser.in_waiting:
        try:
            raw_data = ser.read_all().decode('utf-8', errors='ignore').splitlines()
            if raw_data:
                latest_line = raw_data[-1]
                if "ROLL:" in latest_line:
                    parts = latest_line.split(',')
                    raw_roll = float(parts[0].split(':')[1])
                    if abs(raw_roll) > 0.0001:
                        roll_buffer.append(raw_roll)
                    filtered_roll = median(roll_buffer)
                    setpoint_angle = normalize_angle(math.radians(filtered_roll))
        except Exception:
            pass

    # Krok fizyki
    if dt > 0:
        torque = pid.update(setpoint_angle, satellite.angle_sat, satellite.omega_sat, dt)
        satellite.step(torque, dt)

        sp_deg = math.degrees(setpoint_angle)
        pv_deg = math.degrees(satellite.angle_sat)

        hist_sp.append(sp_deg)
        hist_pv.append(pv_deg)
        hist_wheel_speed.append(satellite.omega_wheel)

        if len(hist_sp) > MAX_HIST:
            hist_sp.pop(0)
            hist_pv.pop(0)
            hist_wheel_speed.pop(0)

    # Scena OpenGL
    glClearColor(0.04, 0.05, 0.08, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glViewport(0, 0, VIEW3D_W, HEIGHT)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    gluPerspective(45, (VIEW3D_W / HEIGHT), 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glShadeModel(GL_SMOOTH)

    glLightfv(GL_LIGHT0, GL_POSITION, [3.0, 4.0, 5.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.98, 0.9, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.22, 0.3, 1.0])

    gluLookAt(0.0, 0.0, 5.5, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

    draw_space_background()
    draw_target_indicator(setpoint_angle)
    draw_satellite_3d(satellite)

    # Panel GUI 2D
    gui_surface.fill((15, 17, 24))
    slider_kp.draw(gui_surface, font_small)
    slider_kd.draw(gui_surface, font_small)
    btn_reset.draw(gui_surface, font_bold)

    draw_chart(gui_surface, pygame.Rect(10, 145, PANEL_W - 20, 145), font_small,
               "Kat Satelity [deg]", -180.0, 180.0,
               [{"data": hist_sp, "color": (80, 220, 120)},
                {"data": hist_pv, "color": (100, 200, 255)}])

    draw_chart(gui_surface, pygame.Rect(10, 300, PANEL_W - 20, 145), font_small,
               "Predkosc Kola [rad/s]", -300.0, 300.0,
               [{"data": hist_wheel_speed, "color": (255, 180, 80)}])

    gui_data = pygame.image.tostring(gui_surface, "RGB", True)

    glViewport(VIEW3D_W, 0, PANEL_W, HEIGHT)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    glOrtho(0, PANEL_W, 0, HEIGHT, -1, 1)
    glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, gui_texture)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, PANEL_W, HEIGHT, 0, GL_RGB, GL_UNSIGNED_BYTE, gui_data)

    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex2f(0, 0)
    glTexCoord2f(1, 0); glVertex2f(PANEL_W, 0)
    glTexCoord2f(1, 1); glVertex2f(PANEL_W, HEIGHT)
    glTexCoord2f(0, 1); glVertex2f(0, HEIGHT)
    glEnd()
    glDisable(GL_TEXTURE_2D)

    pygame.display.flip()
    clock.tick(60)

if ser is not None:
    ser.close()
pygame.quit()