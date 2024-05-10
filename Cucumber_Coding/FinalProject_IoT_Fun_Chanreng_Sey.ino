
#include <Wire.h>
#include <Adafruit_BMP280.h>
#include "Adafruit_SHT4x.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <esp_sleep.h>    
/*********************WiFi and MQTT Broker****************************/
const char* ssid = "TP-LINK_E0BE";
const char* password = "14061653";
const char* mqtt_server = "192.168.1.4";
const int mqtt_port = 1883;
const char* mqtt_Client = "";//ClientID
const char* mqtt_username = "";//Token
const char* mqtt_password = "";//Secret
char msg[200];
WiFiClient espClient;
PubSubClient client(espClient);
/*******************Sensor**********************/
Adafruit_BMP280 bmp; // Define BMP280 Sensor
Adafruit_SHT4x sht4 = Adafruit_SHT4x(); //Define SHT4x Sensor
sensors_event_t humidity, temp;
/**************Structure of Queue**********/
// Define a struct
struct dataRead {
  float Temperature;
  float Humidity;
  float airPressure;
  float airTemperature;
};
TaskHandle_t sendTaskHandle;
TaskHandle_t receiveTaskHandle;
QueueHandle_t Queue; //Define QueueHandle_t

// Conversion factor for microseconds to seconds
const long uS_TO_S_FACTOR = 1000000UL;
// Sleep duration in seconds
const int SLEEP_DURATION = 55;//50 seconds = 1mn
uint8_t counterRestart = 0;
void setup() {
  Serial.begin(115200);
  //Set ESP32's CPU Frequency to 160MHz 
  setCpuFrequencyMhz(80); 
  //Get CPU_Frequency to Verify
  Serial.print("CPU Frequency is: ");
  Serial.print(getCpuFrequencyMhz()); 
  Serial.println(" Mhz");
  // Set up timer as the wake up source
  esp_sleep_enable_timer_wakeup(SLEEP_DURATION * uS_TO_S_FACTOR);
  Wire.begin(41, 40);
  if (bmp.begin(0x76)) { // prepare BMP280 sensor
    Serial.println("BMP280 sensor ready");
  }
  if ( sht4.begin()) { // prepare BMP280 sensor
    Serial.println("SHT4x sensor ready");
  }
    //Connect to WiFi
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi ");
    while (WiFi.status() != WL_CONNECTED) {
      counterRestart++;
      delay(500);
      Serial.print(".");
      if(counterRestart>20){
        ESP.restart();
      }
    }
    Serial.println("\nWiFi Connected");
    //connect client to MQTT Broker
    client.setServer(mqtt_server, mqtt_port);
    if(!client.connected()){
      if (client.connect(mqtt_Client, mqtt_username, mqtt_password)) {
            Serial.println("connected");
          }
    }
    //Create Queue
    Queue = xQueueCreate(100,sizeof(struct dataRead));
    // Create task that consumes the queue.
    xTaskCreate(subspendAllTask, "Subspend_Task", 2048, NULL, 1, NULL);
    xTaskCreate(sendToQueue, "Sender", 2048, NULL, 3, &sendTaskHandle);
    xTaskCreate(receiveFromQueue, "Receiver", 2048, NULL, 2, &receiveTaskHandle);
}

void loop() {
  // The loop function is empty because the tasks handle everything
}
// Task that get data and sends it to the queue
void sendToQueue(void *parameter) {
  while (1) {
    // Read data from sensor
    struct dataRead currentData;
    sht4.getEvent(&humidity, &temp);
    currentData.Temperature =temp.temperature;
    currentData.Humidity = humidity.relative_humidity;
    currentData.airTemperature = bmp.readTemperature();
    currentData.airPressure = bmp.readPressure()/1000;//kPa
    // Send data to the queue
    if (xQueueSend(Queue, &currentData, portMAX_DELAY) != pdPASS) {
      Serial.println("Failed to send data to the queue");
    }
    // delay for 60 second = 1mn
     vTaskDelay(60*1000 / portTICK_PERIOD_MS); 
  }
}
// Task data from the queue
void receiveFromQueue(void *parameter) {
  while (1) {
    // Receive data from the queue
    struct dataRead currentData;
    if (xQueueReceive(Queue, &currentData, portMAX_DELAY) == pdPASS) {
      // Serial.println("Temp data: "+String(currentData.Temperature)+" °C");
      // Serial.println("AirTemp data: "+String(currentData.airTemperature) + " °C");
      // Serial.println("AirPressure data: "+String(currentData.airPressure)+" kPa");
      // Serial.println("Humidity data: "+String(currentData.Humidity)+ " %(RH)");
    }
    if(!client.connected()){
      if (client.connect(mqtt_Client, mqtt_username, mqtt_password)) {
            Serial.println("MQTT connected");
          }
    }
    client.loop();
    String data = "{\"Temperature\":"+String(currentData.Temperature)+",\"Humidity\":"+ String(currentData.Humidity)+",\"Air_Temperature\":"+ String(currentData.airTemperature)+",\"Air_Pressure\":"+ String(currentData.airPressure) + "}";
    Serial.println(data);
    data.toCharArray(msg, (data.length() + 1));
    client.publish("@msg/data", msg);
  }
}
void subspendAllTask(void *pvParameters) {
  while (1) {
    // Task code here
    Serial.println("All tasks will suspend in 1mn");
    // Delay for 5*1000ms
    vTaskDelay(3*1000 / portTICK_PERIOD_MS); 
    // Suspend the task
    vTaskSuspend(sendTaskHandle);
    vTaskSuspend(receiveTaskHandle);
    Serial.println("All tasks is suspended");
    //disconnect WiFi
    WiFi.disconnect(); 
    // Put the ESP32 into deep sleep mode
    Serial.println("Go to Bed now.");
    esp_deep_sleep_start();
  }
}
