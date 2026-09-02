#ifndef MPU6050_CUSTOM_H
#define MPU6050_CUSTOM_H

#include <Arduino.h>
#include <Wire.h>

struct KalmanState {
    float angle = 0.0f;
    float bias = 0.0f;
    float P[2][2] = {{0.0f, 0.0f}, {0.0f, 0.0f}};
};

class MPU6050_Custom {
private:
    uint8_t _addr;
    int _sdaPin;
    int _sclPin;

    KalmanState _kalmanRoll;
    KalmanState _kalmanPitch;

    // Parametry szumu filtra Kalmana
    const float _Q_angle = 0.001f;
    const float _Q_bias = 0.003f;
    const float _R_measure = 0.03f;

    void writeRegister(uint8_t reg, uint8_t data);
    float runKalman(KalmanState &state, float newAngle, float newRate, float dt);

public:
    MPU6050_Custom(uint8_t addr = 0x68);
    bool begin(int sdaPin = 21, int sclPin = 22, uint32_t frequency = 400000);
    
    void readRaw(int16_t &accX, int16_t &accY, int16_t &accZ, 
                 int16_t &gyroX, int16_t &gyroY, int16_t &gyroZ);
                 
    void update(float dt, float &roll, float &pitch);
};

#endif