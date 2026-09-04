import math
import random
from OpenGL.GL import *
from OpenGL.GLU import *
from ui.gl_utils import draw_box, draw_cylinder, draw_grid

# Statyczne tło gwiazd generowane raz przy imporcie modułu
STARS = [(random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-8, -2)) for _ in range(150)]


def apply_material(diffuse, specular=[0.0, 0.0, 0.0, 1.0], shininess=0.0):
    """Pomocnicza funkcja do nakładania właściwości materiału OpenGL."""
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, diffuse)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, specular)
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shininess)


def draw_styled_cylinder(quad, radius, height, slices=32):
    """Rysuje gładki walec z zaślepkami i przeliczonymi wektorami normalnymi."""
    gluQuadricNormals(quad, GLU_SMOOTH)
    
    # Boki walca
    gluCylinder(quad, radius, radius, height, slices, 1)
    
    # Zaślepka dolna
    glPushMatrix()
    glRotatef(180, 1, 0, 0)
    gluDisk(quad, 0, radius, slices, 1)
    glPopMatrix()
    
    # Zaślepka górna
    glPushMatrix()
    glTranslatef(0.0, 0.0, height)
    gluDisk(quad, 0, radius, slices, 1)
    glPopMatrix()


def draw_furuta_3d(furuta, setpoint_arm):
    
    # 1. Siatka podłoża
    draw_grid(size=10, spacing=0.2, z_offset=-0.45)

    # 2. Oświetlenie sceny
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # Subtelne odbicie światła na powierzchniach
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.5, 0.5, 0.5, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 20.0)

    # Światło główne (z góry i z prawej)
    glLightfv(GL_LIGHT0, GL_POSITION, [2.5, 4.0, 3.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.95, 0.95, 0.9, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.25, 0.25, 0.3, 1.0])

    # Światło wypełniające (z lewej - doświetla cienie silnika)
    glLightfv(GL_LIGHT1, GL_POSITION, [-3.0, 2.0, -2.0, 1.0])
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.25, 0.3, 0.35, 1.0])

    quad = gluNewQuadric()
    gluQuadricNormals(quad, GLU_SMOOTH)

    # ---------------------------------------------------------
    # 3. PODSTAWA
    # ---------------------------------------------------------
    glPushMatrix()
    glTranslatef(0.0, -0.4, 0.0)
    glColor3f(0.2, 0.22, 0.28)
    draw_box(0.7, 0.08, 0.7)
    glPopMatrix()

    # ---------------------------------------------------------
    # 4. KORPUS SILNIKA
    # ---------------------------------------------------------
    glPushMatrix()
    glTranslatef(0.0, -0.36, 0.0)
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.35, 0.38, 0.45)
    draw_cylinder(0.14, 0.36)
    glPopMatrix()

    # ---------------------------------------------------------
    # 5. WSKAŹNIK SETPOINT
    # ---------------------------------------------------------
    glPushMatrix()
    glRotatef(math.degrees(setpoint_arm) - 90, 0, 1, 0)
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    glColor3f(0.1, 0.9, 0.4)
    draw_cylinder(0.01, furuta.L_r * 1.15)
    glPopMatrix()
    glPopMatrix()

    # ---------------------------------------------------------
    # 6. RAMIĘ POZIOME
    # ---------------------------------------------------------
    glPushMatrix()
    glRotatef(math.degrees(furuta.theta1) - 90, 0, 1, 0)
    
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    glColor3f(0.2, 0.5, 0.85)
    draw_cylinder(0.035, furuta.L_r)
    glPopMatrix()

    # ---------------------------------------------------------
    # 7. PRZEGUB WAHADŁA
    # ---------------------------------------------------------
    glTranslatef(furuta.L_r, 0.0, 0.0)
    glPushMatrix()
    glRotatef(90, 0, 0, 1)
    glColor3f(0.9, 0.3, 0.2)
    draw_cylinder(0.04, 0.06)
    glPopMatrix()

    # ---------------------------------------------------------
    # 8. WAHADŁO PIONOWE I CIĘŻAREK
    # ---------------------------------------------------------
    glRotatef(math.degrees(furuta.theta2), 1, 0, 0)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    
    # Pręt wahadła
    glColor3f(0.95, 0.95, 0.95)
    draw_cylinder(0.02, furuta.L_p)
    
    # Kula na końcu wahadła (gładka sfera bez przebarwień)
    glTranslatef(0.0, 0.0, furuta.L_p)
    glColor3f(0.9, 0.7, 0.1)
    gluSphere(quad, 0.035, 24, 24)
    
    glPopMatrix()
    glPopMatrix()

    # Sprzątanie
    gluDeleteQuadric(quad)
    glDisable(GL_LIGHTING)

def draw_crane_scene(crane, target_x):
    """Rysuje model 3D Suwnicy / Dźwigu."""
    draw_grid(size=20, spacing=0.2, z_offset=-1.0)

    # Belka suwnicy
    glColor3f(0.4, 0.45, 0.55)
    glPushMatrix()
    glTranslatef(0.0, 1.0, 0.0)
    draw_box(4.6, 0.08, 0.08)
    glPopMatrix()

    # Linia Celu (SP)
    glDisable(GL_LIGHTING)
    glColor3f(0.1, 0.9, 0.4)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex3f(target_x, 1.3, 0.0)
    glVertex3f(target_x, -1.2, 0.0)
    glEnd()
    glEnable(GL_LIGHTING)

    # Wózek
    glPushMatrix()
    glTranslatef(crane.x, 1.0, 0.0)
    glColor3f(0.85, 0.45, 0.15)
    draw_box(0.5, 0.25, 0.3)

    # Lina i Ładunek
    load_x = crane.length * math.sin(crane.theta)
    load_y = -crane.length * math.cos(crane.theta)

    glDisable(GL_LIGHTING)
    glColor3f(0.9, 0.9, 0.95)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(load_x, load_y, 0.0)
    glEnd()
    glEnable(GL_LIGHTING)

    # Masa ładunku
    glTranslatef(load_x, load_y, 0.0)
    glColor3f(0.85, 0.2, 0.2)
    quad = gluNewQuadric()
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluSphere(quad, 0.12, 24, 24)
    gluDeleteQuadric(quad)

    glPopMatrix()


def draw_quadrocopter_scene(drone):
    """Rysuje drona w układzie współrzędnych Z-Up."""
    draw_grid(size=20, spacing=0.2, z_offset=0.0)

    target_x = getattr(drone, 'setpoint_x', 0.0)
    target_y = getattr(drone, 'setpoint_y', 0.0)

    glDisable(GL_LIGHTING)
    glColor4f(0.2, 0.9, 0.4, 0.4)
    glLineWidth(1.5)

    glBegin(GL_LINES)
    glVertex3f(target_x, target_y, 0.0)
    glVertex3f(target_x, target_y, 0.8)
    glEnd()

    glPointSize(10.0)
    glBegin(GL_POINTS)
    glColor3f(0.2, 0.95, 0.4)
    glVertex3f(target_x, target_y, 0.8)
    glEnd()
    glEnable(GL_LIGHTING)

    glPushMatrix()
    x = drone.pos[0]
    y = drone.pos[1]
    z = drone.pos[2] if len(drone.pos) > 2 else 0.8

    glTranslatef(x, y, z)

    phi = getattr(drone, 'phi', 0.0)
    theta = getattr(drone, 'theta', 0.0)

    glRotatef(math.degrees(phi), 1, 0, 0)
    glRotatef(math.degrees(-theta), 0, 1, 0)

    # Korpus główny
    glPushMatrix()
    glScalef(0.08, 0.08, 0.01)
    glColor3f(1.0, 0.5, 0.0)
    draw_box(2.0, 2.0, 2.0)
    glPopMatrix()

    # Centralny akcent
    glPushMatrix()
    glTranslatef(0.0, 0.0, 0.012)
    glScalef(0.04, 0.04, 0.003)
    glColor3f(1.0, 1.0, 0.2)
    draw_box(2.0, 2.0, 2.0)
    glPopMatrix()

    # Bateria
    glPushMatrix()
    glTranslatef(0.0, 0.0, -0.015)
    glScalef(0.045, 0.065, 0.01)
    glColor3f(0.9, 0.9, 0.9)
    draw_box(2.0, 2.0, 2.0)
    glPopMatrix()

    arm = getattr(drone, 'arm_len', 0.25) * 0.75
    rotors = [
        (-arm, -arm, False),
        (arm, -arm, False),
        (-arm, arm, True),
        (arm, arm, True)
    ]

    prop_rot = getattr(drone, 'prop_angle', 0.0)

    for rx, ry, is_front in rotors:
        glPushMatrix()
        if is_front:
            glColor3f(1.0, 0.55, 0.0)
        else:
            glColor3f(0.85, 0.85, 0.9)

        glLineWidth(6)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(rx, ry, 0)
        glEnd()
        glPopMatrix()

        glPushMatrix()
        glTranslatef(rx, ry, 0.0)

        glColor3f(0.3, 0.3, 0.35)
        draw_cylinder(0.018, 0.03)

        glTranslatef(0.0, 0.0, 0.035)
        glRotatef(prop_rot if not is_front else -prop_rot, 0, 0, 1)

        glColor3f(1.0, 0.9, 0.0)
        glLineWidth(4)
        glBegin(GL_LINES)
        glVertex3f(-0.09, 0, 0)
        glVertex3f(0.09, 0, 0)
        glEnd()

        glPopMatrix()

    glPopMatrix()


def draw_ball_and_plate_scene(system):
    """Rysuje układ Piłka na Płytce (Ball & Plate)."""
    draw_grid(size=20, spacing=0.2, z_offset=0.0)

    glPushMatrix()
    
    elevation = getattr(system, 'elevation', 0.5)
    glTranslatef(0.0, 0.0, elevation)

    plate_pitch = getattr(system, 'plate_pitch', 0.0)
    plate_roll = getattr(system, 'plate_roll', 0.0)
    
    glRotatef(-plate_pitch, 0.0, 1.0, 0.0)
    glRotatef(-plate_roll, 1.0, 0.0, 0.0)

    hx = hy = system.plate_size
    hz = system.plate_thickness / 2.0

    glColor3f(0.08, 0.15, 0.25)
    glBegin(GL_QUADS)
    glNormal3f(0.0, 0.0, 1.0)
    glVertex3f(-hx, -hy, hz); glVertex3f(hx, -hy, hz); glVertex3f(hx, hy, hz); glVertex3f(-hx, hy, hz)
    glNormal3f(0.0, 0.0, -1.0)
    glVertex3f(-hx, -hy, -hz); glVertex3f(-hx, hy, -hz); glVertex3f(hx, hy, -hz); glVertex3f(hx, -hy, -hz)
    glNormal3f(0.0, 1.0, 0.0)
    glVertex3f(-hx, hy, -hz); glVertex3f(-hx, hy, hz); glVertex3f(hx, hy, hz); glVertex3f(hx, hy, -hz)
    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(-hx, -hy, -hz); glVertex3f(hx, -hy, -hz); glVertex3f(hx, -hy, hz); glVertex3f(-hx, -hy, hz)
    glNormal3f(1.0, 0.0, 0.0)
    glVertex3f(hx, -hy, -hz); glVertex3f(hx, hy, -hz); glVertex3f(hx, hy, hz); glVertex3f(hx, -hy, hz)
    glNormal3f(-1.0, 0.0, 0.0)
    glVertex3f(-hx, -hy, -hz); glVertex3f(-hx, -hy, hz); glVertex3f(-hx, hy, hz); glVertex3f(-hx, hy, -hz)
    glEnd()

    glLineWidth(3.0)
    glColor3f(0.7, 0.8, 0.9)
    glBegin(GL_LINE_LOOP)
    glVertex3f(-hx, -hy, hz + 0.001)
    glVertex3f(hx, -hy, hz + 0.001)
    glVertex3f(hx, hy, hz + 0.001)
    glVertex3f(-hx, hy, hz + 0.001)
    glEnd()

    glPushMatrix()
    glTranslatef(system.setpoint_x, system.setpoint_y, hz + 0.002)
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

    glPushMatrix()
    glTranslatef(system.ball_pos[0], system.ball_pos[1], hz + system.ball_radius)
    glColor3f(0.95, 0.2, 0.2)
    quad_ball = gluNewQuadric()
    gluQuadricNormals(quad_ball, GLU_SMOOTH)
    gluSphere(quad_ball, system.ball_radius, 24, 24)
    gluDeleteQuadric(quad_ball)
    glPopMatrix()

    glPopMatrix()


# --- ELEMENTY RYSOWANIA DLA SATELITY ---

def _draw_space_background():
    """Rysuje gwieździste tło oraz tarcze orientacyjne."""
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


def _draw_target_indicator(angle):
    """Rysuje żółty wektor celu orientacji."""
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


def _draw_solar_panel():
    """Rysuje pojedynczy panel słoneczny."""
    apply_material([0.15, 0.15, 0.18, 1.0], [0.5, 0.5, 0.5, 1.0], 20.0)
    draw_box(1.4, 0.65, 0.04)

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


def draw_satellite_scene(sat):
    """Rysuje model 3D Satelity z Kołem Reakcyjnym."""
    glDisable(GL_COLOR_MATERIAL)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glShadeModel(GL_SMOOTH)

    glLightfv(GL_LIGHT0, GL_POSITION, [3.0, 4.0, 5.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 0.98, 0.9, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.22, 0.3, 1.0])

    _draw_space_background()
    _draw_target_indicator(sat.setpoint_angle)

    glPushMatrix()
    glRotatef(math.degrees(sat.angle_sat), 0, 0, 1)

    quad = gluNewQuadric()
    gluQuadricNormals(quad, GLU_SMOOTH)

    # 1. Główny korpus
    apply_material([0.25, 0.27, 0.3, 1.0], [0.8, 0.8, 0.9, 1.0], 50.0)
    draw_box(0.9, 0.9, 0.5)

    # 2. Złota osłona termiczna (MLI)
    apply_material([0.9, 0.7, 0.1, 1.0], [1.0, 0.9, 0.4, 1.0], 90.0)
    draw_box(0.92, 0.4, 0.52)

    # 3. Panele słoneczne
    glPushMatrix()
    glTranslatef(-1.25, 0, 0)
    _draw_solar_panel()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(1.25, 0, 0)
    _draw_solar_panel()
    glPopMatrix()

    # 4. Wysięgniki paneli
    apply_material([0.6, 0.6, 0.65, 1.0], [0.9, 0.9, 0.9, 1.0], 30.0)
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side * 0.5, 0, 0)
        glRotatef(90, 0, 1, 0)
        gluCylinder(quad, 0.025, 0.025, 0.1, 12, 1)
        glPopMatrix()

    # 5. Przód Satelity (Optyka / Sensor)
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

    # 6. Tył Satelity - Antena
    glPushMatrix()
    glTranslatef(-0.46, 0, 0)
    glRotatef(-90, 0, 1, 0)
    apply_material([0.85, 0.85, 0.85, 1.0], [1.0, 1.0, 1.0, 1.0], 40.0)
    gluCylinder(quad, 0.02, 0.18, 0.12, 16, 1)
    glPopMatrix()

    # 7. Koło Reakcyjne
    glPushMatrix()
    glTranslatef(0, 0, 0.25)

    apply_material([0.12, 0.14, 0.18, 1.0], [0.3, 0.3, 0.3, 1.0], 10.0)
    gluCylinder(quad, 0.38, 0.38, 0.04, 32, 1)

    glTranslatef(0, 0, 0.04)
    glRotatef(math.degrees(sat.angle_wheel), 0, 0, 1)

    apply_material([0.3, 0.32, 0.38, 1.0], [0.8, 0.8, 0.9, 1.0], 60.0)
    gluCylinder(quad, 0.12, 0.12, 0.08, 24, 1)
    gluDisk(quad, 0, 0.12, 24, 1)

    apply_material([0.85, 0.65, 0.15, 1.0], [1.0, 0.85, 0.4, 1.0], 80.0)
    gluCylinder(quad, 0.36, 0.36, 0.08, 32, 1)
    gluDisk(quad, 0.26, 0.36, 32, 1)

    apply_material([0.2, 0.22, 0.25, 1.0], [0.5, 0.5, 0.5, 1.0], 30.0)
    for i in range(4):
        glPushMatrix()
        glRotatef(i * 90, 0, 0, 1)
        glTranslatef(0.19, 0, 0.04)
        draw_box(0.16, 0.04, 0.03)
        glPopMatrix()

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