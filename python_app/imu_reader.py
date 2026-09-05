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

        # Bufory do filtrowania medianowego dla obu osi
        self.roll_buffer = deque([0.0] * 5, maxlen=5)
        self.pitch_buffer = deque([0.0] * 5, maxlen=5)

        self.latest_roll = 0.0
        self.latest_pitch = 0.0

        self._connect()

    def _connect(self):
        """Próba połączenia z portem szeregowym."""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=getattr(config, 'SERIAL_TIMEOUT', 0.01))
            print(f"[SERIAL] Połączono z {self.port}")
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            print(f"[SERIAL] Brak portu {self.port} (Tryb bez sprzętu IMU): {e}")
            self.ser = None

    def _read_loop(self):
        """Pętla wykonywana w osobnym wątku do stałego odczytu portu COM."""
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting:
                    raw_data = self.ser.read_all().decode('utf-8', errors='ignore').splitlines()
                    if raw_data:
                        latest_line = raw_data[-1]
                        
                        # Oczekiwana ramka: "ROLL:12.34,PITCH:-5.67" lub podobny format
                        if "ROLL:" in latest_line:
                            parts = latest_line.split(',')
                            
                            # Odczyt ROLL
                            for part in parts:
                                if "ROLL:" in part:
                                    raw_roll = float(part.split(':')[1])
                                    if abs(raw_roll) > 0.0001:
                                        self.roll_buffer.append(raw_roll)
                                        self.latest_roll = median(self.roll_buffer)
                                
                                # Odczyt PITCH (jeśli występuje w ramce)
                                elif "PITCH:" in part:
                                    raw_pitch = float(part.split(':')[1])
                                    if abs(raw_pitch) > 0.0001:
                                        self.pitch_buffer.append(raw_pitch)
                                        self.latest_pitch = median(self.pitch_buffer)

            except Exception:
                pass
            time.sleep(0.005)  # Odpoczynek wątku (odświeżanie ~200 Hz)

    def get_roll(self):
        """Zwraca najnowszą, przefiltrowaną wartość ROLL."""
        return self.latest_roll

    def get_pitch(self):
        """Zwraca najnowszą, przefiltrowaną wartość PITCH."""
        return self.latest_pitch

    def get_orientation(self):
        """Zwraca krotkę (roll, pitch)."""
        return self.latest_roll, self.latest_pitch

    def is_connected(self):
        """Zwraca True, jeśli port Serial jest aktywny."""
        return self.ser is not None and self.ser.is_open

    def close(self):
        """Zamknięcie połączenia i wątku."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.2)
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[SERIAL] Połączenie zamknięte.")