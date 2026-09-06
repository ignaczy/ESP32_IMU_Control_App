import math
from OpenGL.GL import *
from OpenGL.GLU import *

def draw_box(dx, dy, dz):
    """Renders a 3D box (cuboid) centered at the origin with specified dimensions."""
    hx, hy, hz = dx / 2.0, dy / 2.0, dz / 2.0
    glBegin(GL_QUADS)
    
    # Top face
    glNormal3f(0.0, 1.0, 0.0)
    glVertex3f(-hx, hy, -hz); glVertex3f(-hx, hy, hz); glVertex3f(hx, hy, hz); glVertex3f(hx, hy, -hz)
    # Bottom face
    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(-hx, -hy, -hz); glVertex3f(hx, -hy, -hz); glVertex3f(hx, -hy, hz); glVertex3f(-hx, -hy, hz)
    # Front face
    glNormal3f(0.0, 0.0, 1.0)
    glVertex3f(-hx, -hy, hz); glVertex3f(hx, -hy, hz); glVertex3f(hx, hy, hz); glVertex3f(-hx, hy, hz)
    # Back face
    glNormal3f(0.0, 0.0, -1.0)
    glVertex3f(-hx, hy, -hz); glVertex3f(hx, hy, -hz); glVertex3f(hx, -hy, -hz); glVertex3f(-hx, -hy, -hz)
    # Left face
    glNormal3f(-1.0, 0.0, 0.0)
    glVertex3f(-hx, -hy, -hz); glVertex3f(-hx, -hy, hz); glVertex3f(-hx, hy, hz); glVertex3f(-hx, hy, -hz)
    # Right face
    glNormal3f(1.0, 0.0, 0.0)
    glVertex3f(hx, -hy, hz); glVertex3f(hx, -hy, -hz); glVertex3f(hx, hy, -hz); glVertex3f(hx, hy, hz)
    glEnd()

def draw_cylinder(radius, height, slices=24):
    """Renders a closed cylinder along the Z-axis including top and bottom caps."""
    quadric = gluNewQuadric()
    gluCylinder(quadric, radius, radius, height, slices, 1)
    
    # Bottom cap
    glPushMatrix()
    glRotatef(180, 1, 0, 0)
    gluDisk(quadric, 0, radius, slices, 1)
    glPopMatrix()
    
    # Top cap
    glPushMatrix()
    glTranslatef(0, 0, height)
    gluDisk(quadric, 0, radius, slices, 1)
    glPopMatrix()
    
    gluDeleteQuadric(quadric)

def draw_grid(size=20, spacing=0.2, z_offset=0.0):
    """Renders a horizontal reference grid floor in the XY plane."""
    glDisable(GL_LIGHTING)
    glColor4f(0.2, 0.25, 0.35, 0.4)
    glLineWidth(1)

    limit = size * spacing
    glBegin(GL_LINES)
    for i in range(-size, size + 1):
        coord = i * spacing
        # Parallel lines along Y-axis
        glVertex3f(coord, -limit, z_offset)
        glVertex3f(coord, limit, z_offset)

        # Parallel lines along X-axis
        glVertex3f(-limit, coord, z_offset)
        glVertex3f(limit, coord, z_offset)
    glEnd()

    glEnable(GL_LIGHTING)