#include <Ticker.h>
#include "wifimanage.h"
#include "otatool.h"
#include "common.h"
#include "DHT.h"

//https://randomnerdtutorials.com/esp8266-dht11dht22-temperature-and-humidity-web-server-with-arduino-ide/
//DHT11温湿度传感器

String DEVICE    =      "mydht11";
#define LED            2
#define PIN          0
#define LEDON           LOW
#define LEDOFF          HIGH


#define DHTTYPE DHT11   // DHT 11
//#define DHTTYPE DHT21   // DHT 21 (AM2301)
//#define DHTTYPE DHT22   // DHT 22  (AM2302), AM2321

Ticker btn_timer;
Ticker led_timer;

unsigned long count = 0;                                     // (Do not Change)
bool sendStatus = false;                                     // (Do not Change)
bool requestRestart = false;                                 // (Do not Change)
bool hasmqtt = false;
String currentIP;

String MQTT_TOPIC = "";

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

const int DHTPin = 0;
DHT dht(DHTPin, DHTTYPE);

void setup()
{
  Serial.begin(115200);
  Serial.println("start......");
  setVersion(firmversion);
  setdevicetype(DEVICE);
  
  int ch = StartInit();
  Serial.print("ReadResetTimes:");
  Serial.println(ch);
  if (ch > 5 ) {
    StartError();
  }
  
  pinMode(LED, OUTPUT);
  led_timer.attach(0.5, blink);
  
  startWifi();  //连接网络信息
  initOTA(LED);// 初使化OTA模式

  String MQTT_TOPIC = "home/" + DEVICE + "/" + readID();
  initMQTT(MQTT_TOPIC, callback);

  StartFinish();

  led_timer.detach();
  digitalWrite(LED, LEDON); //灯常亮，表示连接成功
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
}

void blinkLED(int pin, int duration, int n) {
  for (int i = 0; i < n; i++)  {
    digitalWrite(pin, HIGH);
    delay(duration);
    digitalWrite(pin, LOW);
    delay(duration);
  }
}

int oldstat = -1;

//按钮处理
void button() {
  //  try {
  //            float newT = dht.readHumidity();
  //    if (isnan(newT)) {
  //      Serial.println("Failed to read from DHT sensor!newT");
  //    }
  //    else {
  //      Serial.println(newT);
  //    }

  //    float newH = dht.readHumidity();
  //    if (isnan(newH)) {
  //      Serial.println("Failed to read from DHT sensor!newH");
  //    }
  //    else {
  //      Serial.println(newH);
  //    }
  //  }
  //  catch (const std::exception& ex)
  //  {
  //    Serial.printf("Error:%s", ex.what());
  //
  //  }

  //  int newstat = digitalRead(PIN);
  //  if (newstat != oldstat){ //有变化发送至mq
  //      sendStatus = true;
  //
  ////      if (newstat == HIGH)
  ////        digitalWrite(LED, LEDON); //亮起
  ////      else
  ////        digitalWrite(LED, LEDOFF); //亮起
  //  }
  //  oldstat = newstat;

}

void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqttClient.connect(readID().c_str())) {
      Serial.println("connected");
      MQTT_TOPIC = "home/" + DEVICE + "/" + readID();
      mqttClient.subscribe(MQTT_TOPIC.c_str());
      Serial.println("Topic:" + MQTT_TOPIC);
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);// Wait 5 seconds before retrying
    }
  }
}


void callback(char* topic, byte * payload, unsigned int length) {
  String payload_string = "";
  for (int i = 0; i < length; ++i)
    payload_string += char(payload[i]);
  Serial.println("receive:" + payload_string);

  if (payload_string == "stat") {
    sendStatus = true;
  }
  else if (payload_string == "reset") {
    blinkLED(LED, 400, 4);
    ESP.restart();
  }
  if (payload_string == "ip") {
    String path = MQTT_TOPIC + "/ip";
    mqttClient.publish(path.c_str(), currentIP.c_str());
  }
}

int kUpdFreq = 1;                                            // Update frequency in Mintes to check for mqtt connection
int kRetries = 10;                                           // WiFi retry count. Increase if not connecting to router.
unsigned long TTasks;
void timedTasks() {
  if ((millis() > TTasks + (kUpdFreq * 60000)) || (millis() < TTasks)) {
    TTasks = millis();
    checkConnection();
  }
}

void checkConnection() {
  if (WiFi.status() != WL_CONNECTED) {
    ESP.restart();
  }
}

int times = 0;

float oldt = 0;
float oldh = 0;
static char celsiusTemp[7];
static char humidityTemp[7];
static char fahrenheitTemp[7];

void loop() {
  if (loopOTA())
    return ;

  timedTasks();

  wifiloop();

  if (hasmqtt && !mqttClient.connected()) {
    connectMQTT();
  }

  if (times == 100) {
    times = 0;
    //每秒读一次，不能放timer中，会挂
    float h = dht.readHumidity();
    float t = dht.readTemperature();

    Serial.print("Humidity: ");
    Serial.print(h);
    Serial.print(" %\t Temperature: ");
    Serial.print(t);
    Serial.print(" *C ");
    Serial.println("");

    if (h != oldh || t != oldt) {
      sendStatus = true;
    }
    oldh = h;
    oldt = t;
  }

  times = times + 1;
  delay(100);

  if (sendStatus) { //发送至mq
    //    float f = dht.readTemperature(true);
    //    float hic = dht.computeHeatIndex(oldt, oldh, false);
    dtostrf(oldt, 6, 2, celsiusTemp);
    //    float hif = dht.computeHeatIndex(f, oldh);
    //    dtostrf(hif, 6, 2, fahrenheitTemp);
    dtostrf(oldh, 6, 2, humidityTemp);

    String path = MQTT_TOPIC + "/Temperature";
    mqttClient.publish(path.c_str(), celsiusTemp);
    String path2 = MQTT_TOPIC + "/Humidity";
    mqttClient.publish(path2.c_str(), humidityTemp);
    Serial.println("statsend . . . . . . . . . . . . . . . . . . ");
    sendStatus = false;
  }

  mqttClient.loop();
}
