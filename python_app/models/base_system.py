from abc import ABC, abstractmethod

class BaseSystem(ABC):
    @abstractmethod
    def reset(self):
        """Resetuje stan układu do wartości początkowych."""
        pass

    @abstractmethod
    def step(self, dt):
        """Wykonuje krok fizyki i oblicza sygnał sterujący."""
        pass

    @abstractmethod
    def draw_3d(self):
        """Rysuje obiekt w oknie OpenGL."""
        pass

    @abstractmethod
    def get_widgets(self):
        """Zwraca listę widgetów UI (suwaki, przyciski) specyficznych dla tego układu."""
        pass

    @abstractmethod
    def get_charts_data(self):
        """Zwraca słownik danych potrzebnych do wygenerowania wykresów w UI."""
        pass

    @abstractmethod
    def set_target_from_input(self, norm_x):
        """Ustawia zadany punkt (setpoint) na podstawie kliknięcia myszą w scenie 3D."""
        pass