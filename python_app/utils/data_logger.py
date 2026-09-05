import csv
import os
from datetime import datetime


class DataLogger:
    def __init__(self):
        self.is_recording = False
        self.recorded_data = []
        self.start_time = 0.0
        self.headers = []

    def start_recording(self, current_time):
        """Rozpoczyna nagrywanie danych."""
        self.is_recording = True
        self.recorded_data.clear()
        self.start_time = current_time

    def stop_and_save(self, system_name="system") -> str:
        """
        Zatrzymuje nagrywanie i zapisuje zebrane dane do pliku CSV.
        Zwraca ścieżkę do zapisanego pliku lub None w przypadku braku danych.
        """
        self.is_recording = False
        if not self.recorded_data or not self.headers:
            return None

        # Ścieżka do folderu logs w głównym katalogu projektu
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(logs_dir, f"{system_name.lower()}_log_{timestamp}.csv")

        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(self.headers)
                writer.writerows(self.recorded_data)
            print(f"[DataLogger] Dane zostały zapisane do pliku: {filename}")
            return filename
        except Exception as e:
            print(f"[DataLogger] Błąd podczas zapisu CSV: {e}")
            return None

    def _extract_numeric_val(self, item):
        """Pomocnicza funkcja wyciągająca ostatnią wartość numeryczną ze słownika/listy."""
        if isinstance(item, dict):
            buf = item.get("data", [])
            item = buf[-1] if len(buf) > 0 else 0.0

        if isinstance(item, (list, tuple)):
            item = item[-1] if len(item) > 0 else 0.0

        try:
            return float(item)
        except (ValueError, TypeError):
            return None

    def _is_valid_chart_key(self, key: str) -> bool:
        """Sprawdza, czy dany klucz odpowiada właściwym danym wykresu, a nie metadanym UI."""
        ignored_keywords = ["status", "color", "title", "text"]
        key_lower = str(key).lower()
        return not any(kw in key_lower for kw in ignored_keywords)

    def sample(self, current_time, system):
        """Pobiera pojedynczą próbkę stanu systemu, jeśli nagrywanie jest aktywne."""
        if not self.is_recording:
            return

        elapsed_time = current_time - self.start_time
        row = [f"{elapsed_time:.4f}"]

        if hasattr(system, "get_charts_data"):
            charts_data = system.get_charts_data()

            # 1. Budowanie nagłówków przy pierwszej próbce (z pominięciem kluczy statusu/koloru)
            if not self.headers:
                self.headers = ["Time [s]"]
                for chart_key, series_list in charts_data.items():
                    if not self._is_valid_chart_key(chart_key):
                        continue

                    if isinstance(series_list, list):
                        for idx, series in enumerate(series_list):
                            val = self._extract_numeric_val(series)
                            if val is not None:
                                self.headers.append(f"{chart_key}_series_{idx + 1}")
                    else:
                        val = self._extract_numeric_val(series_list)
                        if val is not None:
                            self.headers.append(f"{chart_key}")

            # 2. Pobieranie wartości dla właściwych kolumn
            for chart_key, series_list in charts_data.items():
                if not self._is_valid_chart_key(chart_key):
                    continue

                if isinstance(series_list, list):
                    for series in series_list:
                        val = self._extract_numeric_val(series)
                        if val is not None:
                            row.append(f"{val:.4f}")
                else:
                    val = self._extract_numeric_val(series_list)
                    if val is not None:
                        row.append(f"{val:.4f}")

        self.recorded_data.append(row)