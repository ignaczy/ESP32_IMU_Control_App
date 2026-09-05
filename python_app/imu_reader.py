import serial
import threading
import time
from collections import deque
from statistics import median
import config


class IMUReader:
    def __init__(self, port=config.SERIAL_PORT, baudrate=config.BAUD_RATE):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = False
        self.thread = None

        # Pobranie rozmiaru okna mediany z konfiguracji (domyślnie 5 próbek)
        self.window_size = getattr(config, "IMU_MEDIAN_WINDOW_SIZE", 5)

        # Bufery kołowe dla filtru medianowego
        self.roll_buffer = deque([0.0] * self.window_size, maxlen=self.window_size)
        self.pitch_buffer = deque([0.0] * self.window_size, maxlen=self.window_size)

        self.latest_roll = 0.0
        self.latest_pitch = 0.0

        self._connect()

    def _connect(self):
        """Próba połączenia z portem szeregowym."""
        try:
            self.ser = serial.Serial(
                self.port,
                self.baudrate,
                timeout=getattr(config, "SERIAL_TIMEOUT", 0.01),
            )
            print(f"[SERIAL] Połączono z {self.port}")
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            print(f"[SERIAL] Brak portu {self.port} (Tryb bez sprzętu IMU): {e}")
            self.ser = None

    def _apply_median_filter(self, val, buffer):
        """Pomocnicza metoda aktualizująca bufor i wyliczająca medianę."""
        buffer.append(val)
        return median(buffer)

    def _read_loop(self):
        """Pętla wykonywana w osobnym wątku do stałego odczytu i filtrowania danych."""
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting:
                    raw_data = (
                        self.ser.read_all()
                        .decode("utf-8", errors="ignore")
                        .splitlines()
                    )
                    if raw_data:
                        latest_line = raw_data[-1]

                        # Przetwarzanie ramki danych: "ROLL:12.34,PITCH:-5.67"
                        if "ROLL:" in latest_line or "PITCH:" in latest_line:
                            parts = latest_line.split(",")

                            for part in parts:
                                part = part.strip()

                                # Filtrowanie osi ROLL
                                if "ROLL:" in part:
                                    try:
                                        raw_roll = float(part.split(":")[1])
                                        self.latest_roll = self._apply_median_filter(
                                            raw_roll, self.roll_buffer
                                        )
                                    except ValueError:
                                        pass

                                # Filtrowanie osi PITCH
                                elif "PITCH:" in part:
                                    try:
                                        raw_pitch = float(part.split(":")[1])
                                        self.latest_pitch = self._apply_median_filter(
                                            raw_pitch, self.pitch_buffer
                                        )
                                    except ValueError:
                                        pass

            except Exception:
                pass

            time.sleep(0.005)  # Odpowiednik odświeżania ~200 Hz

    def get_roll(self):
        """Zwraca najnowszą, przefiltrowaną wartość ROLL (stopnie)."""
        return self.latest_roll

    def get_pitch(self):
        """Zwraca najnowszą, przefiltrowaną wartość PITCH (stopnie)."""
        return self.latest_pitch

    def get_orientation(self):
        """Zwraca spójną krotkę (roll, pitch) poddaną filtracji medianowej."""
        return self.latest_roll, self.latest_pitch

    def is_connected(self):
        """Zwraca True, jeśli port Serial jest aktywny."""
        return self.ser is not None and self.ser.is_open

    def close(self):
        """Bezpieczne zamknięcie połączenia i wątku."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.2)
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[SERIAL] Połączenie zamknięte.")