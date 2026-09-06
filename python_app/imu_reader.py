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

        # Fetch median filter window size from configuration (defaults to 5 samples)
        self.window_size = getattr(config, "IMU_MEDIAN_WINDOW_SIZE", 5)

        # Circular buffers for the median filter
        self.roll_buffer = deque([0.0] * self.window_size, maxlen=self.window_size)
        self.pitch_buffer = deque([0.0] * self.window_size, maxlen=self.window_size)

        self.latest_roll = 0.0
        self.latest_pitch = 0.0

        self._connect()

    def _connect(self):
        """Attempts to establish connection with the serial port."""
        try:
            self.ser = serial.Serial(
                self.port,
                self.baudrate,
                timeout=getattr(config, "SERIAL_TIMEOUT", 0.01),
            )
            print(f"[SERIAL] Connected to {self.port}")
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
        except Exception as e:
            print(f"[SERIAL] Port {self.port} unavailable (Fallback to hardware-less mode): {e}")
            self.ser = None

    def _apply_median_filter(self, val, buffer):
        """Helper method to update the circular buffer and calculate the median."""
        buffer.append(val)
        return median(buffer)

    def _read_loop(self):
        """Background thread loop for continuous data reading and filtering."""
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

                        # Parsing telemetry frame: "ROLL:12.34,PITCH:-5.67"
                        if "ROLL:" in latest_line or "PITCH:" in latest_line:
                            parts = latest_line.split(",")

                            for part in parts:
                                part = part.strip()

                                # Filtering ROLL axis
                                if "ROLL:" in part:
                                    try:
                                        raw_roll = float(part.split(":")[1])
                                        self.latest_roll = self._apply_median_filter(
                                            raw_roll, self.roll_buffer
                                        )
                                    except ValueError:
                                        pass

                                # Filtering PITCH axis
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

            time.sleep(0.005)  # Polling frequency equivalent to ~200 Hz

    def get_roll(self):
        """Returns the latest filtered ROLL value (in degrees)."""
        return self.latest_roll

    def get_pitch(self):
        """Returns the latest filtered PITCH value (in degrees)."""
        return self.latest_pitch

    def get_orientation(self):
        """Returns a tuple (roll, pitch) containing the latest filtered orientation."""
        return self.latest_roll, self.latest_pitch

    def is_connected(self):
        """Returns True if the Serial connection is active."""
        return self.ser is not None and self.ser.is_open

    def close(self):
        """Safely terminates the background thread and closes the serial connection."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.2)
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[SERIAL] Connection closed.")