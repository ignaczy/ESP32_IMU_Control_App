# 🚀 ESP32 IMU Control Systems Lab

![ESP32](https://img.shields.io/badge/ESP32-323330?style=for-the-badge&logo=espressif&logoColor=white)
![C++](https://img.shields.io/badge/C%2B%2B-00599C?style=for-the-badge&logo=c%2B%2B&logoColor=white)
![PlatformIO](https://img.shields.io/badge/PlatformIO-F6821F?style=for-the-badge&logo=platformio&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenGL](https://img.shields.io/badge/OpenGL-5586A4?style=for-the-badge&logo=opengl&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-Green?style=for-the-badge&logo=python&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c?style=for-the-badge&logo=python&logoColor=white)

<p align="center">
  <b>An advanced, real-time 3D physical simulation and control engineering testbed.</b><br>
  Integrates <b>Hardware-in-the-Loop (HIL)</b> dynamic stabilization via an <b>ESP32 + MPU6050 IMU</b> controller with high-fidelity OpenGL interactive rendering and data logging features.
</p>

---

## 🎬 Demo

<p align="center">
  <img src="assets/demo.gif" alt="Simulation Demo">
</p>

---

## 📌 Things to Do 

- [ ] **Tune controllers and add new ones (e.g., Swing-up for Furuta)**
- [ ] **Trajectory Tracking**
- [ ] **Disturbance Injector**
- [ ] **Add new control systems**

---

## 🌟 Key Features

* **Real-Time 3D Visualization:** Powered by OpenGL and Pygame for smooth rendering of physical system dynamics.
* **Hardware-in-the-Loop (HIL) via Serial (UART):** Real-time orientation angle streaming (Roll/Pitch) from an ESP32 connected to an MPU6050 IMU sensor, fused using a Kalman filter for precise tilt estimation.
* **Real-Time Data Logging:** Interactive recording of telemetry and control signals directly from the 3D viewport, exported automatically to `.csv` format.
* **Data Visualization Tool:** Built-in standalone Matplotlib script for post-simulation time-series analysis with synchronized time axes.
* **PID & State-Space Control:** Fully interactive tuning of parameters via UI sliders.
* **Signal Filtering:** Integrated median filtering to eliminate noisy IMU sensor measurements.
* **Manual & Fallback Control:** Seamless mouse and keyboard control modes when no physical hardware is connected.

---

## 🎛️ Interactive Simulation Models

1. **🏗️ Crane Anti-Sway Control**
   * Overhead crane simulation with a suspended payload.
   * Anti-sway stabilization algorithms damping payload oscillations during trolley movement.
2. **🌀 Furuta Pendulum (Rotary Inverted Pendulum)**
   * Non-linear rotary inverted pendulum stabilized around the top unstable equilibrium position using state feedback control.
3. **🛸 Quadrocopter (1D/2D Pitch/Roll PID)**
   * Position tracking and pitch/roll tilt angle stabilization based on real-time IMU sensor telemetry.
4. **⚪ Ball and Plate**
   * Two-axis ball positioning on a flat plate using decoupled dual-loop PID controllers.
5. **🛰️ Satellite (Reaction Wheel Control)**
   * Single-axis satellite orientation control using reaction wheel momentum exchange.

---

## 📊 Data Logging & Plotting Utilities

* **In-App CSV Recorder (`DataLogger`):** Toggle recording at any moment using the bottom-left button in the 3D viewport. Automatically filters out UI metadata and exports real-time trajectories (Setpoint, Process Variable, Control Action) to the `logs/` directory.
* **Automatic Chart Generator (`plot_csv.py`):** Universal Matplotlib script located in `utils/`. Automatically locates the latest CSV log file, parses all dynamic data series, and generates publication-ready stacked time-series plots.

---

## 🔌 Hardware Setup & Pinout

To run in **Hardware-in-the-Loop (HIL)** mode, connect the MPU6050 IMU to the ESP32 via I2C:

| MPU6050 Pin | ESP32 GPIO | Description |
| :---: | :---: | :--- |
| **VCC** | 3.3V | Power Supply |
| **GND** | GND | Ground |
| **SCL** | GPIO 22 | I2C Clock |
| **SDA** | GPIO 21 | I2C Data |

---

## 🛠️ Project Architecture

```text
ESP32_IMU_Control_App/
│
├── assets/                      # Demo of App
├── documentation/               # Mathematical, Physical, and Control Documentation
├── lib/                         # Custom MPU6050 driver library with Kalman Filter
├── src/                         # [C++] ESP32 firmware source code
│   └── main.cpp                 # Reads MPU6050 telemetry & streams formatted data over UART
├── platformio.ini               # PlatformIO environment & dependency settings
│
├── logs/                        # Automatically generated CSV telemetry logs
│
├── python_app/                  # [Python] Simulation engine & 3D renderer
│   ├── models/                  # Physics engines and mathematical models 
│   ├── ui/                      # GUI, HUD elements, charts, and 3D overlay widgets
│   ├── utils/                   # Data processing and analysis scripts
│   │
│   ├── config.py                # Global parameters, target FPS, and COM configuration
│   ├── serial_handler.py        # UART serial communication manager
│   ├── simulation.py            # Main simulation execution loop
│   └── main.py                  # Application entry point and mode selector
│
├── .gitignore
├── LICENSE
├── requirements.txt
└── README.md
```

---

## 📦 Requirements & Installation

### 1. Python Environment
Requires **Python 3.10+**.

Install all necessary libraries:
```bash
pip install -r requirements.txt
```

### 2. Firmware Flashing (PlatformIO)
1. Connect your ESP32 board equipped with an MPU6050 IMU to your PC.
2. Open the project root in VS Code with the PlatformIO extension installed.
3. Build and flash the firmware using PlatformIO: Upload.

---

## 🚀 Getting Started

1. Ensure the correct serial port is specified in python_app/config.py (e.g., COM8 or /dev/ttyUSB0).
2. Run the main simulation app:
```bash
cd python_app
python main.py
```

3. Plotting Logged Data:
   After recording data during a simulation session, run the automated visualization script:
```bash
python python_app/utils/plot_csv.py
```

---

## ⌨️ Controls & Shortcuts

* START / STOP REJESTRACJI Button (Bottom-Left Viewport): Starts real-time telemetry logging and saves output to logs/.
* Mouse (LMB): Set target positions directly on the 3D viewport or adjust PID sliders (Kp, Ki, Kd) on the control panel.
* SPACE: Reset current system state and clear target position.
* ESC: Return to the main simulation selection menu.


---

## 📚 Technical Documentation

A comprehensive mathematical, physical, and control theoretical documentation for all implemented systems is available in PDF format:

📄 **[Control Systems Technical Report](documentation/Control_system_report.pdf)**

### Documentation Coverage:
* **Rigorous Mathematical Derivations:** Full Euler-Lagrange kinetic and dynamic equations of motion for all 5 testbeds.
* **Control Theory Analysis:** State-space models, linear state-feedback design, dual-loop cascade structures, and anti-windup architectures.
* **System Identification & Parameters:** Explicit tables listing physical masses, inertia matrices, friction terms, and operational constraints.

---

## 👤 Author

* Ignacy Glura – https://github.com/ignaczy

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.