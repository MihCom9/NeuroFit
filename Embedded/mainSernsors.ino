#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BMP280.h>
#include <Wire.h>
#include <TinyGPS++.h>
#include <WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#define GPS_BAUD 9600
#define GPSRx 16
#define GPSTx 17
#define callButt 18
#define UVLightPin 27
#define BuzzerPin 14

Adafruit_MPU6050 mpu;

TinyGPSPlus gps;

const char* ssid = "Mino";
const char* password = "AGoodPass";
const char* serverAddress = "192.168.10.188";
const char* webSocketIp = "192.168.10.173";
const int websocketPort=8080;
const int serverPort = 8080;
WebSocketsClient webSocket;
unsigned long previousMillis = 0;  // Variable to store last time data was sent
const long interval = 2000;

Adafruit_BMP280 bmp;

// Reference height (at the point where you start measuring)
float referenceHeight = 0.8; // Adjust this to the initial height in meters
float handHeight = 0;
float distanceGround=0;
float currentAltitude = 0;

const int numReadings = 10; // Number of readings to average for smoothing
float altitudeReadings[numReadings]; // Array to store readings for averaging
int readingIndex = 0;  // Index for the array
float totalAltitude = 0; // Total of all altitude readings

float referenceAltitude = 0; // Variable to store the reference altitude
float totalReferenceAltitude = 0; // Total of all reference altitude readings
int referenceIndex = 0;  // Index for the reference altitude array

unsigned long lastUpdateTime = 0;
unsigned long updateInterval = 5000; // Update the reference altitude every 10 seconds


const float referenceVoltageUV=3.3;
float uvIntensity;

sensors_event_t accel, gyro, temp;
double longtitude,latitude,altitude;
uint8_t timeHour,timeMinute,timeSecond;

float accelX_offset=0,accelY_offset=0,accelZ_offset=0,gyroX_offset=0,gyroY_offset=0,gyroZ_offset=0;
HardwareSerial gpsSerial(2);

int stepCount = 0;
bool stepDetected = false;
float previousAccZ = 0;
float stepThreshold = 1.5; // Threshold for step detection
float stepLength = 0.73;
float totalDistance = 0;
float prevMagnitude = 0;

float gyroDegX=0,gyroDegY=0,gyroDegZ=0;
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_CONNECTED:
            Serial.println("Connected to WebSocket server");
            // webSocket.sendTXT("Hello from ESP32");  // Send a test message after connection
            break;
        case WStype_DISCONNECTED:
            Serial.println("Disconnected from WebSocket server");
            break;
        case WStype_TEXT:
            // This block will handle any text message received
            Serial.print("Received Message: ");
            Serial.println((char*)payload);  // Print received message
            delay(10);
            break;
        case WStype_BIN:
            Serial.println("Received binary data");
            break;
        case WStype_ERROR:
            Serial.println("WebSocket error occurred");
            break;
    }
}
void checkDistance(void* params){
  while(1){
    if (millis() - lastUpdateTime >= updateInterval && abs(handHeight * 100) < 15) {
      referenceAltitude = bmp.readAltitude();  // Update reference altitude
      lastUpdateTime = millis();  // Reset the timer

      Serial.print("Updated Reference Altitude: ");
      Serial.println(referenceAltitude);
    }

    // Remove the oldest reading from the total altitude
    totalAltitude -= altitudeReadings[readingIndex];

    // Read current altitude from BMP280
    float newAltitude = bmp.readAltitude();  // Read the altitude (in meters)

    // Add the new reading to the total and update the array
    altitudeReadings[readingIndex] = newAltitude;
    totalAltitude += newAltitude;

    // Move to the next index in the array
    readingIndex = (readingIndex + 1) % numReadings;

    // Calculate the average altitude
    float averagedAltitude = totalAltitude / numReadings;
  
    // Calculate the hand's height relative to the reference
    handHeight = averagedAltitude - referenceAltitude;
  
    distanceGround=referenceHeight+handHeight;

    // Output the results
    Serial.print("Current Altitude: ");
    Serial.print(averagedAltitude);
    Serial.print(" m, Hand Height: ");
    Serial.print(handHeight * 100); // Convert to centimeters
    Serial.print(" cm, Distance to floor: ");
    Serial.print(distanceGround * 100);
    Serial.println(" cm");

    // Wait for a short delay before the next reading
    vTaskDelay(pdMS_TO_TICKS(36));
  }
}
void detectStep(float accX, float accY, float accZ) {
  // Calculate the magnitude of acceleration (independent of orientation)
  float magnitude = sqrt(accX * accX + accY * accY + accZ * accZ);

  if (!stepDetected && (magnitude - prevMagnitude) > 1.2) { 
    stepCount++;
    totalDistance += stepLength;

    Serial.print("Steps: ");
    Serial.print(stepCount);
    Serial.print(" | Distance: ");
    Serial.print(totalDistance);
    Serial.println(" meters");

    stepDetected = true;
  } 
  else if ((magnitude - prevMagnitude) < 0.5) {
    stepDetected = false;
  }

  prevMagnitude = magnitude;
}
void readMpu6050(){
  mpu.getEvent(&accel, &gyro, &temp);
  accel.acceleration.x-=accelX_offset;
  accel.acceleration.y-=accelY_offset;
  accel.acceleration.z-=accelZ_offset;

  gyro.gyro.x-=gyroX_offset;
  gyro.gyro.y-=gyroY_offset;
  gyro.gyro.z-=gyroZ_offset;

  /* Print out the values */
  Serial.print("Acceleration X: ");
  Serial.print(accel.acceleration.x);
  Serial.print(", Y: ");
  Serial.print(accel.acceleration.y);
  Serial.print(", Z: ");
  Serial.print(accel.acceleration.z);
  Serial.println(" m/s^2");

  Serial.print("Rotation X: ");
  Serial.print(gyro.gyro.x);
  Serial.print(", Y: ");
  Serial.print(gyro.gyro.y);
  Serial.print(", Z: ");
  Serial.print(gyro.gyro.z);
  Serial.println(" rad/s");

  Serial.print("Temperature: ");
  Serial.print(temp.temperature);
  Serial.println(" degC");

  Serial.println("");
  detectStep(accel.acceleration.z,accel.acceleration.x,accel.acceleration.y);
  gyroDegX=gyro.gyro.x*(180.0/PI);
  gyroDegY=gyro.gyro.y*(180.0/PI);
  gyroDegZ=gyro.gyro.z*(180.0/PI);
}
void getAccelData(void* params){
  while(1){
    readMpu6050();
    vTaskDelay(pdMS_TO_TICKS(50));
  }
}
void gpsRead(){

  unsigned long start = millis();

  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }
  if (gps.location.isUpdated()) {
      latitude=gps.location.isValid() ? gps.location.lat() : 0.0;
      Serial.print("Latitude: "); 
      Serial.print(latitude);
      longtitude=gps.location.isValid() ? gps.location.lng() : 0.0;
      Serial.print(" Longitude: "); 
      Serial.print(longtitude);
      altitude=gps.altitude.isValid() ? gps.altitude.meters() : 0.0;
      Serial.print(" Altitude: "); 
      Serial.print(altitude);
      Serial.print(" meters");
      Serial.println();

      Serial.print("Satellites: "); 
      Serial.println(gps.satellites.value());
      timeHour=gps.time.hour();
      timeHour+=2;
      if(timeHour>24){
        timeHour=24-timeHour;
      }
      timeMinute=gps.time.minute();
      timeSecond=gps.time.second();
      Serial.print("Time: ");
      Serial.print(timeHour);
      Serial.print(":");
      Serial.print(timeMinute);
      Serial.print(":");
      Serial.print(timeSecond);
      Serial.println();
    }
}
void checkCallibraion(){
  if(digitalRead(callButt)){
    Serial.println("Button callibration clicked");
    Serial.println("Button callibration clicked");
    Serial.println("Button callibration clicked");
    long accelX_sum = 0, accelY_sum = 0, accelZ_sum = 0;
    long gyroX_sum = 0, gyroY_sum = 0, gyroZ_sum = 0;
    int readings = 30;  // Number of readings to average

    for (int i = 0; i < readings; i++) {
      sensors_event_t accel, gyro, temp;
      mpu.getEvent(&accel, &gyro, &temp);

      accelX_sum += accel.acceleration.x;
      accelY_sum += accel.acceleration.y;
      accelZ_sum += accel.acceleration.z;

      gyroX_sum += gyro.gyro.x;
      gyroY_sum += gyro.gyro.y;
      gyroZ_sum += gyro.gyro.z;

      delay(10);  // Short delay between readings
    }

    // Calculate the average values to get the offsets
    accelX_offset = accelX_sum / readings;
    accelY_offset = accelY_sum / readings;
    accelZ_offset = accelZ_sum / readings;
    
    gyroX_offset = gyroX_sum / readings;
    gyroY_offset = gyroY_sum / readings;
    gyroZ_offset = gyroZ_sum / readings;

    // Adjust for the accelerometer reading (expect 0G for X and Y, 1G for Z when stationary)
    accelZ_offset = accelZ_offset - 9.81;  // Adjust Z-axis to represent gravity (9.81 m/s^2)
  }
}
void readUVLight(){
  int uvReading = analogRead(UVLightPin); 
  float voltage = (uvReading / 4095.0) * referenceVoltageUV;  
  uvIntensity = (voltage - 0.99) * (15.0 / 1.8);  

  if(uvIntensity<0){
    uvIntensity=0;
  }
  // Serial.print("UV Voltage: ");
  // Serial.print(voltage);
  // Serial.println(" V");

  // Serial.print("UV Intensity: ");
  // Serial.print(uvIntensity);
  // Serial.println(" mW/cm²");
}
void readSensors(void *params){
  while(1){
    checkCallibraion();
    readUVLight();
    gpsRead();
    vTaskDelay(500 / portTICK_PERIOD_MS);
  }
}
void sendWebsocket(void *params){
  while(1){
    webSocket.loop();  // Maintain WebSocket connection
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval) {
      // Save the last time we sent data
      previousMillis = currentMillis;
      String disp="Acceleration: ";
      disp+=String(accel.acceleration.x)+" ";
      disp+=String(accel.acceleration.y)+" ";
      disp+=String(accel.acceleration.z)+" ";
      disp+=" rad/s^2\n\n";
      disp+="Rotation: ";
      disp+=String(gyro.gyro.x)+ " ";
      disp+=String(gyro.gyro.y)+ " ";
      disp+=String(gyro.gyro.z)+ " ";
      disp+=" m/s^2\n\n";
      disp+="Temperature: ";
      disp+=String(temp.temperature);
      disp+=" degC\n\n";
      disp+="Latitude: ";
      disp+=String(latitude)+"\n\n";
      disp+="Longtitude: ";
      disp+=String(longtitude)+"\n\n";
      disp+="Altitude: ";
      disp+=String(altitude)+"\n\n";
      disp+="Time: ";
      disp+=String(timeHour)+":"+String(timeMinute)+":"+String(timeSecond)+"\n\n";
      disp+="UVIntensity: ";
      disp+=String(uvIntensity)+"\n\n";
      webSocket.sendTXT(disp);  // Send distance data via WebSocket
    }
    vTaskDelay(10 / portTICK_PERIOD_MS);
  }
}
void sendHttpRequest(void *params) {
  while (1) {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;

      // Create JSON object
      StaticJsonDocument<256> jsonDoc;
      jsonDoc["acceleration_x"] = accel.acceleration.x;
      jsonDoc["acceleration_y"] = accel.acceleration.y;
      jsonDoc["acceleration_z"] = accel.acceleration.z;
      jsonDoc["rotation_x"] = gyroDegX;
      jsonDoc["rotation_y"] = gyroDegY;
      jsonDoc["rotation_z"] = gyroDegZ;
      jsonDoc["temperature"] = temp.temperature;
      jsonDoc["latitude"] = latitude;
      jsonDoc["longitude"] = longtitude;
      jsonDoc["altitude"] = altitude;
      jsonDoc["steps"]= stepCount;
      //@TODO add the uv intensity here!!!

      // Serialize JSON to string
      String jsonPayload;
      serializeJson(jsonDoc, jsonPayload);

      // Send HTTP POST request
      HTTPClient http;
      String serverURL = "http://" + String(serverAddress) + ":" + String(serverPort) + "/data";  // Adjust endpoint
      http.begin(serverURL);
      http.addHeader("Content-Type", "application/json");

      int httpResponseCode = http.POST(jsonPayload);
      if (httpResponseCode > 0) {
        Serial.print("HTTP1 Response code: ");
        Serial.println(httpResponseCode);
      } else {
        Serial.print("HTTP1 Error: ");
        Serial.println(httpResponseCode);
      }
      http.end();
      HTTPClient http2;
      serverURL = "http://" + String(webSocketIp) + ":" + String(websocketPort) + "/data";  // Adjust endpoint
      http2.begin(serverURL);
      http2.addHeader("Content-Type", "application/json");

      httpResponseCode = http2.POST(jsonPayload);
      if (httpResponseCode > 0) {
        Serial.print("HTTP2 Response code: ");
        Serial.println(httpResponseCode);
      } else {
        Serial.print("HTTP2 Error: ");
        Serial.println(httpResponseCode);
      }
      http2.end();
    }
    vTaskDelay(100 / portTICK_PERIOD_MS);
  }
}

void setup(void) {
  Serial.begin(115200);
  pinMode(callButt, INPUT_PULLDOWN);
  pinMode(UVLightPin,INPUT);
  pinMode(BuzzerPin, OUTPUT);
  WiFi.begin(ssid, password);
  // Connect to WiFi
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
      delay(1000);
      Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  // webSocket.begin(webSocketIp, websocketPort, "/");  // Connect to the WebSocket server
  // webSocket.onEvent(webSocketEvent);  // Attach event handler
  Serial.println("Adafruit MPU6050 test!");

  // Try to initialize!
  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {
      delay(10);
    }
  }
  Serial.println("MPU6050 Found!");

  mpu.setAccelerometerRange(MPU6050_RANGE_16_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_5_HZ);
  if (!bmp.begin(0x76)) {
    Serial.println("BMP280 not found!");
    while (1);
  }

  bmp.setSampling(Adafruit_BMP280::MODE_NORMAL,     // Continuous mode
                  Adafruit_BMP280::SAMPLING_X8,    // Temp oversampling x16
                  Adafruit_BMP280::SAMPLING_X8,    // Pressure oversampling x16
                  Adafruit_BMP280::FILTER_X8,      // IIR filter x16 to reduce noise
                  Adafruit_BMP280::STANDBY_MS_1);  // 63ms between readings

  // Set the initial reference altitude using the first reading
  referenceAltitude = bmp.readAltitude();  // Read the initial altitude
  Serial.print("Initial Reference Altitude: ");
  Serial.println(referenceAltitude);

  // Initialize the altitudeReadings array
  for (int i = 0; i < numReadings; i++) {
    altitudeReadings[i] = currentAltitude;
    totalAltitude += altitudeReadings[i];
  }

  gpsSerial.begin(GPS_BAUD,SERIAL_8N1,GPSRx,GPSTx);
  xTaskCreatePinnedToCore(readSensors,"Reading sensors function",2000,NULL, 1, NULL, 0);
  xTaskCreatePinnedToCore(checkDistance, "Distance to floor check",2000, NULL, 1, NULL,0);
  xTaskCreatePinnedToCore(getAccelData, "Mpu6050 data",2000, NULL, 1, NULL,0);
  xTaskCreatePinnedToCore(sendHttpRequest,"Sends data to website",10000,NULL, 2, NULL, 1);
  // xTaskCreatePinnedToCore(sendWebsocket,"Sends data to website with websocket",10000,NULL, 1, NULL, 1);
}
void loop() {
  /* Get new sensor events with the readings */
  vTaskDelay(1000 / portTICK_PERIOD_MS);
}