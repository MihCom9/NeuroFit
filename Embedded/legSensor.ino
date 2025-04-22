#include <Wire.h>
#include <MPU6050_light.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP280.h>
#include <esp_now.h>
#include <WiFi.h>

// Define sensor objects
MPU6050 mpu(Wire);
Adafruit_BMP280 bmp;  // I2C

// Gravitational constant
const float GRAVITY = 9.81;

// Define structure for sending data
typedef struct {
  float accX_ms2;
  float accY_ms2;
  float accZ_ms2;
  float gyroX_dps;
  float gyroY_dps;
  float gyroZ_dps;
  float altitude_m;
} SensorData;

SensorData sensorData;

// Define peer address globally
uint8_t peerAddress[] = { 0xE8, 0x31, 0xCD, 0x31, 0x94, 0xF4 };  // Replace with the MAC address of the receiver E8:31:CD:31:94:F4

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Initialize MPU6050
  byte status = mpu.begin();
  Serial.print("MPU init status: ");
  Serial.println(status); // 0 = success

  if (status != 0) {
    Serial.println("⚠️ MPU6050 not initialized. Check wiring or chip.");
    while (1);
  }

  // Initialize BMP280
  if (!bmp.begin(0x76)) {
    Serial.println("⚠️ Could not find a valid BMP280 sensor.");
    while (1);
  }

  Serial.println("MPU6050 and BMP280 initialized!");

  // Initialize ESP-NOW
  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Set up ESP-NOW peer (this would be the MAC address of the receiving ESP device)
  esp_now_peer_info_t peerInfo;
  memcpy(peerInfo.peer_addr, peerAddress, 6);
  peerInfo.channel = 0;  // Default channel
  peerInfo.encrypt = false;
  peerInfo.ifidx = WIFI_IF_STA;  // ✅ CRUCIAL!
  // Add peer to ESP-NOW
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add peer");
    return;
  }

  delay(1000);
  mpu.calcOffsets(); // Optional: auto-calibrate MPU6050

  // Print out the MAC address of this device (sender)
  Serial.print("Sender MAC address: ");
  Serial.println(WiFi.macAddress());
}

void sendData() {
  // Check if the sensors are working correctly before sending data
    // Convert acceleration to m/s²
    sensorData.accX_ms2 = mpu.getAccX() * GRAVITY;
    sensorData.accY_ms2 = mpu.getAccY() * GRAVITY;
    sensorData.accZ_ms2 = mpu.getAccZ() * GRAVITY;

    // Read pressure from BMP280 and calculate altitude
    float pressure = bmp.readPressure() / 100.0F;  // Pressure in hPa
    sensorData.altitude_m = bmp.readAltitude(1013.25); // Use standard sea-level pressure
    Serial.print("Altitude: ");
    Serial.println(sensorData.altitude_m);
    // Read gyroscope values in degrees per second
    sensorData.gyroX_dps = mpu.getGyroX();
    sensorData.gyroY_dps = mpu.getGyroY();
    sensorData.gyroZ_dps = mpu.getGyroZ();

    // Send data using ESP-NOW
    esp_err_t result = esp_now_send(peerAddress, (uint8_t*)&sensorData, sizeof(sensorData));

    if (result == ESP_OK) {
      Serial.println("Data sent successfully.");
    } else {
      Serial.println("Error sending data.");
    }
}

void loop() {
  mpu.update();
  sendData();
  Serial.println("--------------------------------------------------");

  delay(50);
}
