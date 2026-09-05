import pygame
from pygame.locals import DOUBLEBUF, OPENGL

import config
from imu_reader import IMUReader
from ui.main_menu import show_selection_menu
from simulation import run_simulation


def main():
    pygame.init()
    screen = pygame.display.set_mode(
        (config.WINDOW_WIDTH, config.WINDOW_HEIGHT), DOUBLEBUF | OPENGL
    )
    pygame.display.set_caption("Control Systems Lab")

    clock = pygame.time.Clock()
    font_small = pygame.font.SysFont("Segoe UI", 12)

    imu = IMUReader()

    try:
        while True:
            selected_mode = show_selection_menu(screen, clock)
            result = run_simulation(selected_mode, screen, clock, font_small, imu)

            if result == "QUIT":
                break
    finally:
        imu.close()
        pygame.quit()


if __name__ == "__main__":
    main()