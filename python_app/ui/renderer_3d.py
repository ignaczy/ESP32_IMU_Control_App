import math
from OpenGL.GL import *
from OpenGL.GLU import *

def draw_cylinder(radius, height, slices=24):
    """Rysuje walec w osi Z o danej wysokości i promieniu."""
    quadric = gluNewQuadric()
    gluCylinder(quadric, radius, radius, height, slices, 1)
    
    # Podstawa dolna
    glPushMatrix()
    glRotatef(180, 1, 0, 0)
    gluDisk(quadric, 0, radius, slices, 1)
    glPopMatrix()
    
    # Podstawa górna
    glPushMatrix()
    glTranslatef(0, 0, height)
    gluDisk(quadric, 0, radius, slices, 1)
    glPopMatrix()
    
    gluDeleteQuadric(quadric)

def draw_box(dx, dy, dz):
    """Rysuje prostopadłościan o zadanych wymiarach skrajnych."""
    hx, hy, hz = dx / 2.0, dy / 2.0, dz / 2.0
    glBegin(GL_QUADS)
    
    # Górna ściana
    glNormal3f(0, 1, 0)
    glVertex3f(-hx, hy, -hz); glVertex3f(-hx, hy, hz); glVertex3f(hx, hy, hz); glVertex3f(hx, hy, -hz)
    
    # Dolna ściana
    glNormal3f(0, -1, 0)
    glVertex3f(-hx, -hy, -hz); glVertex3f(hx, -hy, -hz); glVertex3f(hx, -hy, hz); glVertex3f(-hx, -hy, hz)
    
    # Przednia ściana
    glNormal3f(0, 0, 1)
    glVertex3f(-hx, -hy, hz); glVertex3f(hx, -hy, hz); glVertex3f(hx, hy, hz); glVertex3f(-hx, hy, hz)
    
    # Tylna ściana
    glNormal3f(0, 0, -1)
    glVertex3f(-hx, hy, -hz); glVertex3f(hx, hy, -hz); glVertex3f(hx, -hy, -hz); glVertex3f(-hx, -hy, -hz)
    
    # Lewa ściana
    glNormal3f(-1, 0, 0)
    glVertex3f(-hx, -hy, -hz); glVertex3f(-hx, -hy, hz); glVertex3f(-hx, hy, hz); glVertex3f(-hx, hy, -hz)
    
    # Prawa ściana
    glNormal3f(1, 0, 0)
    glVertex3f(hx, -hy, hz); glVertex3f(hx, -hy, -hz); glVertex3f(hx, hy, -hz); glVertex3f(hx, hy, hz)
    
    glEnd()

def draw_grid():
    """Rysuje siatkę pomocniczą na podłożu."""
    glDisable(GL_LIGHTING)
    glColor4f(0.2, 0.25, 0.35, 0.5)
    glLineWidth(1)
    glBegin(GL_LINES)
    for i in range(-10, 11):
        glVertex3f(i * 0.2, -0.45, -2.0)
        glVertex3f(i * 0.2, -0.45, 2.0)
        glVertex3f(-2.0, -0.45, i * 0.2)
        glVertex3f(2.0, -0.45, i * 0.2)
    glEnd()
    glEnable(GL_LIGHTING)

def draw_furuta_3d(furuta, setpoint_arm):
    """Rysuje kompletny model 3D Wahadła Furuty."""
    draw_grid()

    # Oświetlenie sceny
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glLightfv(GL_LIGHT0, GL_POSITION, [2.0, 3.5, 2.5, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.9, 0.95, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.25, 0.25, 0.3, 1.0])

    # Podstawa
    glPushMatrix()
    glTranslatef(0.0, -0.4, 0.0)
    glColor3f(0.2, 0.22, 0.28)
    draw_box(0.7, 0.08, 0.7)
    glPopMatrix()

    # Korpus silnika
    glPushMatrix()
    glTranslatef(0.0, -0.36, 0.0)
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.35, 0.38, 0.45)
    draw_cylinder(0.14, 0.36)
    glPopMatrix()

    # Wskaźnik zadanego kąta ramienia (Zielona linia)
    glPushMatrix()
    glRotatef(math.degrees(setpoint_arm) - 90, 0, 1, 0)
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    glColor3f(0.1, 0.9, 0.4)
    draw_cylinder(0.01, furuta.L_r * 1.15)
    glPopMatrix()
    glPopMatrix()

    # Ramię główne (obrót -90 deg ustawia ramię przodem do obserwatora)
    glPushMatrix()
    glRotatef(math.degrees(furuta.theta1) - 90, 0, 1, 0)
    glPushMatrix()
    glRotatef(90, 0, 1, 0)
    glColor3f(0.2, 0.5, 0.85)
    draw_cylinder(0.035, furuta.L_r)
    glPopMatrix()

    # Przegub
    glTranslatef(furuta.L_r, 0.0, 0.0)
    glPushMatrix()
    glRotatef(90, 0, 0, 1)
    glColor3f(0.9, 0.3, 0.2)
    draw_cylinder(0.04, 0.06)
    glPopMatrix()

    # Wahadło
    glRotatef(math.degrees(furuta.theta2), 1, 0, 0)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.95, 0.95, 0.95)
    draw_cylinder(0.02, furuta.L_p)
    
    # Masa końcowa wahadła
    glTranslatef(0.0, 0.0, furuta.L_p)
    glColor3f(0.9, 0.7, 0.1)
    quad = gluNewQuadric()
    gluSphere(quad, 0.035, 16, 16)
    glPopMatrix()

    glPopMatrix()
    glDisable(GL_LIGHTING)