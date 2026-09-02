import serial
import config

ser = None

def init_serial():
    global ser
    try:
        ser = serial.Serial(
            config.SERIAL_PORT,
            config.BAUD_RATE,
            timeout=getattr(config, "SERIAL_TIMEOUT", 0.01),
        )
        print(f"[SERIAL] Połączono z {config.SERIAL_PORT}")
    except Exception as e:
        print(f"[SERIAL] Brak portu {config.SERIAL_PORT} (Tryb ręczny): {e}")
        ser = None
    return ser

def close_serial():
    global ser
    if ser is not None:
        ser.close()