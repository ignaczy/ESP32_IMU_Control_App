from abc import ABC, abstractmethod

class BaseSystem(ABC):
    @abstractmethod
    def reset(self):
        """Resets the system state to initial values."""
        pass

    @abstractmethod
    def step(self, dt):
        """Executes a physics step and calculates the control signal."""
        pass

    @abstractmethod
    def draw_3d(self):
        """Renders the object in the OpenGL window."""
        pass

    @abstractmethod
    def get_widgets(self):
        """Returns a list of UI widgets (sliders, buttons) specific to this system."""
        pass

    @abstractmethod
    def get_charts_data(self):
        """Returns a dictionary of data required to generate charts in the UI."""
        pass

    @abstractmethod
    def set_target_from_input(self, norm_x):
        """Sets the desired setpoint based on a mouse click in the 3D scene."""
        pass