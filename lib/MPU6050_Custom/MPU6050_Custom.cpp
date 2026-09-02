#include "MPU6050_Custom.h"
#include <math.h>

MPU6050_Custom::MPU6050_Custom(uint8_t addr) : _addr(addr) {}

void MPU6050_Custom::writeRegister(uint8_t reg, uint8_t data) {
    Wire.beginTransmission(_addr);
    Wire.write(reg);
    Wire.write(data);
    Wire.endTransmission();
}

bool MPU6050_Custom::begin(int sdaPin, int sclPin, uint32_t frequency) {
    _sdaPin = sdaPin;
    _sclPin = sclPin;

    Wire.begin(_sdaPin, _sclPin, frequency);

    Wire.beginTransmission(_addr);
    if (Wire.endTransmission() != 0) {
        return false;
    }

    // Wybudzenie MPU6050 z trybu uśpienia (PWR_MGMT_1 = 0)
    writeRegister(0x6B, 0x00);
    delay(50);

    // Ustawienie zakresu akcelerometru (±2g) i żyroskopu (±250 deg/s)
    writeRegister(0x1C, 0x00); 
    writeRegister(0x1B, 0x00);

    return true;
}

void MPU6050_Custom::readRaw(int16_t &accX, int16_t &accY, int16_t &accZ, 
                             int16_t &gyroX, int16_t &gyroY, int16_t &gyroZ) {
    Wire.beginTransmission(_addr);
    Wire.write(0x3B); // Odczyt rejestrów od 0x3B (ACCEL_XOUT_H)
    Wire.endTransmission(false);

    Wire.requestFrom(_addr, (uint8_t)14, (uint8_t)true);

    if (Wire.available() >= 14) {
        accX = (Wire.read() << 8) | Wire.read();
        accY = (Wire.read() << 8) | Wire.read();
        accZ = (Wire.read() << 8) | Wire.read();
        Wire.read(); Wire.read(); // Pominięcie temperatury
        gyroX = (Wire.read() << 8) | Wire.read();
        gyroY = (Wire.read() << 8) | Wire.read();
        gyroZ = (Wire.read() << 8) | Wire.read();
    }
}

float MPU6050_Custom::runKalman(KalmanState &state, float newAngle, float newRate, float dt) {
    // 1. Predykcja
    float rate = newRate - state.bias;
    state.angle += dt * rate;

    state.P[0][0] += dt * (dt * state.P[1][1] - state.P[0][1] - state.P[1][0] + _Q_angle);
    state.P[0][1] -= dt * state.P[1][1];
    state.P[1][0] -= dt * state.P[1][1];
    state.P[1][1] += _Q_bias * dt;

    // 2. Korekcja
    float S = state.P[0][0] + _R_measure;

    if (S == 0.0f || isnan(S)) {
        S = 0.0001f;
    }

    float K[2];
    K[0] = state.P[0][0] / S;
    K[1] = state.P[1][0] / S;

    float y = newAngle - state.angle;
    state.angle += K[0] * y;
    state.bias  += K[1] * y;

    float P00_temp = state.P[0][0];
    float P01_temp = state.P[0][1];

    state.P[0][0] -= K[0] * P00_temp;
    state.P[0][1] -= K[0] * P01_temp;
    state.P[1][0] -= K[1] * P00_temp;
    state.P[1][1] -= K[1] * P01_temp;

    return state.angle;
}

void MPU6050_Custom::update(float dt, float &roll, float &pitch) {
    int16_t ax, ay, az, gx, gy, gz;
    readRaw(ax, ay, az, gx, gy, gz);

    // Przeliczenie surowych danych akcelerometru na radiany i przeliczenie kątów
    float accRoll  = atan2((float)ay, (float)az) * RAD_TO_DEG;
    float accPitch = atan2(-(float)ax, sqrt((float)ay * ay + (float)az * az)) * RAD_TO_DEG;

    // Konwersja żyroskopu na deg/s (dla zakrasu ±250 deg/s dzielnik wynosi 131.0)
    float gyroXrate = (float)gx / 131.0f;
    float gyroYrate = (float)gy / 131.0f;

    // Zapobieganie osobliwości (gimbal lock) przy gwałtownym obrocie
    if ((accRoll < -90.0f && _kalmanRoll.angle > 90.0f) || (accRoll > 90.0f && _kalmanRoll.angle < -90.0f)) {
        _kalmanRoll.angle = accRoll;
    } else {
        roll = runKalman(_kalmanRoll, accRoll, gyroXrate, dt);
    }

    if (abs(_kalmanRoll.angle) > 90.0f) {
        gyroYrate = -gyroYrate;
    }
    pitch = runKalman(_kalmanPitch, accPitch, gyroYrate, dt);
}