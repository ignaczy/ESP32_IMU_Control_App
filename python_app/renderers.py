import math
from OpenGL.GL import *
from OpenGL.GLU import *

def draw_cube(size_x, size_y, size_z):
    hx, hy, hz = size_x / 2.0, size_y / 2.0, size_z / 2.0
    glBegin(GL_QUADS)
    glNormal3f(0.0, 0.0, 1.0)
    glVertex3f(-hx, -hy, hz)
    glVertex3f(hx, -hy, hz)
    glVertex3f(hx, hy, hz)
    glVertex3f(-hx, hy, hz)

    glNormal3f(0.0, 0.0, -1.0)
    glVertex3f(-hx, -hy, -hz)
    glVertex3f(-hx, hy, -hz)
    glVertex3f(hx, hy, -hz)
    glVertex3f(hx, -hy, -hz)

    glNormal3f(0.0, 1.0, 0.0)
    glVertex3f(-hx, hy, -hz)
    glVertex3f(-hx, hy, hz)
    glVertex3f(hx, hy, hz)
    glVertex3f(hx, hy, -hz)

    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(-hx, -hy, -hz)
    glVertex3f(hx, -hy, -hz)
    glVertex3f(hx, -hy, hz)
    glVertex3f(-hx, -hy, hz)

    glNormal3f(1.0, 0.0, 0.0)
    glVertex3f(hx, -hy, -hz)
    glVertex3f(hx, hy, -hz)
    glVertex3f(hx, hy, hz)
    glVertex3f(hx, -hy, hz)

    glNormal3f(-1.0, 0.0, 0.0)
    glVertex3f(-hx, -hy, -hz)
    glVertex3f(-hx, -hy, hz)
    glVertex3f(-hx, hy, hz)
    glVertex3f(-hx, hy, -hz)
    glEnd()

def draw_grid():
    glDisable(GL_LIGHTING)
    glColor4f(0.2, 0.25, 0.35, 0.4)
    glLineWidth(1)
    glBegin(GL_LINES)
    for i in range(-20, 21):
        coord = i * 0.2
        glVertex3f(coord, -4.0, 0.0)
        glVertex3f(coord, 4.0, 0.0)
        glVertex3f(-4.0, coord, 0.0)
        glVertex3f(4.0, coord, 0.0)
    glEnd()
    glEnable(GL_LIGHTING)

def draw_crane_scene(crane, target_x):
    draw_grid()

    glColor3f(0.4, 0.45, 0.55)
    glPushMatrix()
    glTranslatef(0.0, 1.0, 0.0)
    draw_cube(4.6, 0.08, 0.08)
    glPopMatrix()

    glDisable(GL_LIGHTING)
    glColor3f(0.1, 0.9, 0.4)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex3f(target_x, 1.3, 0.0)
    glVertex3f(target_x, -1.2, 0.0)
    glEnd()
    glEnable(GL_LIGHTING)

    glPushMatrix()
    glTranslatef(crane.x, 1.0, 0.0)
    glColor3f(0.85, 0.45, 0.15)
    draw_cube(0.5, 0.25, 0.3)

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

    glTranslatef(load_x, load_y, 0.0)
    glColor3f(0.85, 0.2, 0.2)
    quad = gluNewQuadric()
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluSphere(quad, 0.12, 24, 24)

    glPopMatrix()