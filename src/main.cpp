#include <Arduino.h>
#include "MPU6050_Custom.h"

MPU6050_Custom mpu;
unsigned long lastTime = 0;

void setup() {
    Serial.begin(115200);
    while (!Serial);

    if (!mpu.begin(21, 22)) { // Default I2C pins for ESP32: SDA=21, SCL=22
        Serial.println("MPU6050 initialization failed!");
        while (1) { delay(10); }
    }
    
    lastTime = micros();
}

void loop() {
    unsigned long currentTime = micros();
    float dt = (currentTime - lastTime) / 1000000.0f;
    lastTime = currentTime;

    float roll = 0.0f;
    float pitch = 0.0f;

    mpu.update(dt, roll, pitch);

    // Stream over UART in a human-readable format for the 3D visualizer
    Serial.print("ROLL:");
    Serial.print(roll, 2);
    Serial.print(",PITCH:");
    Serial.println(pitch, 2);

    delay(10); // Loop rate approximately 100Hz
}