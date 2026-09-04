import math
from OpenGL.GL import *
from OpenGL.GLU import *

def draw_box(dx, dy, dz):
    """Rysuje prostopadłościan o zadanych wymiarach skrajnych."""
    hx, hy, hz = dx / 2.0, dy / 2.0, dz / 2.0
    glBegin(GL_QUADS)
    
    # Górna
    glNormal3f(0.0, 1.0, 0.0)
    glVertex3f(-hx, hy, -hz); glVertex3f(-hx, hy, hz); glVertex3f(hx, hy, hz); glVertex3f(hx, hy, -hz)
    # Dolna
    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(-hx, -hy, -hz); glVertex3f(hx, -hy, -hz); glVertex3f(hx, -hy, hz); glVertex3f(-hx, -hy, hz)
    # Przednia
    glNormal3f(0.0, 0.0, 1.0)
    glVertex3f(-hx, -hy, hz); glVertex3f(hx, -hy, hz); glVertex3f(hx, hy, hz); glVertex3f(-hx, hy, hz)
    # Tylna
    glNormal3f(0.0, 0.0, -1.0)
    glVertex3f(-hx, hy, -hz); glVertex3f(hx, hy, -hz); glVertex3f(hx, -hy, -hz); glVertex3f(-hx, -hy, -hz)
    # Lewa
    glNormal3f(-1.0, 0.0, 0.0)
    glVertex3f(-hx, -hy, -hz); glVertex3f(-hx, -hy, hz); glVertex3f(-hx, hy, hz); glVertex3f(-hx, hy, -hz)
    # Prawa
    glNormal3f(1.0, 0.0, 0.0)
    glVertex3f(hx, -hy, hz); glVertex3f(hx, -hy, -hz); glVertex3f(hx, hy, -hz); glVertex3f(hx, hy, hz)
    glEnd()

def draw_cylinder(radius, height, slices=24):
    """Rysuje walec w osi Z z podstawami."""
    quadric = gluNewQuadric()
    gluCylinder(quadric, radius, radius, height, slices, 1)
    
    glPushMatrix()
    glRotatef(180, 1, 0, 0)
    gluDisk(quadric, 0, radius, slices, 1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, 0, height)
    gluDisk(quadric, 0, radius, slices, 1)
    glPopMatrix()
    
    gluDeleteQuadric(quadric)

def draw_grid(size=20, spacing=0.2, z_offset=0.0):
    """Rysuje poziomą podłogę w płaszczyźnie XY (dla układu gdzie Z to wysokość)."""
    glDisable(GL_LIGHTING)
    glColor4f(0.2, 0.25, 0.35, 0.4)
    glLineWidth(1)

    limit = size * spacing
    glBegin(GL_LINES)
    for i in range(-size, size + 1):
        coord = i * spacing
        # Linie biegnące wzdłuż osi Y
        glVertex3f(coord, -limit, z_offset)
        glVertex3f(coord, limit, z_offset)

        # Linie biegnące wzdłuż osi X
        glVertex3f(-limit, coord, z_offset)
        glVertex3f(limit, coord, z_offset)
    glEnd()

    glEnable(GL_LIGHTING)