#include <Ticker.h>
#include "src/commonlib/wifimanage.h"
#include "src/commonlib/otatool.h"
#include "src/commonlib/common.h"
#include "DHT.h"

//https://randomnerdtutorials.com/esp8266-dht11dht22-temperature-and-humidity-web-server-with-arduino-ide/
//DHT11温湿度传感器

String firmversion =    "2.2";
String DEVICE    =      "mydht11";

#define LED            2
#define PIN          0
#define LEDON           LOW
#define LEDOFF          HIGH

Ticker led_timer;
boolean sendStatus = false;

#define DHTTYPE DHT11   // DHT 11
//#define DHTTYPE DHT21   // DHT 21 (AM2301)
//#define DHTTYPE DHT22   // DHT 22  (AM2302), AM2321
DHT dht(PIN, DHTTYPE);

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

  //String MQTT_TOPIC = "home/" + DEVICE + "/" + readID();
  String MQTT_TOPIC = "homeassistant/sensor";// + readID();
  initMQTT(MQTT_TOPIC, "/set", false, callback);

  StartFinish();

  String cfg = String("{");
  cfg += "\"device_class\": \"temperature\"";
  cfg += ",\"name\": \"" + readID() + "_T\"";
  cfg += ",\"unique_id\": \"" + readID() + "_T\"";
  cfg += ",\"state_topic\": \"homeassistant/sensor/" + readID() + "/state\"";
  cfg += ",\"unit_of_measurement\": \"°C\"";
  cfg += ",\"value_template\": \"{{ value_json.temperature}}\"";
  cfg += "}";

  Serial.println(cfg);
  sendmqtt("/" + readID() + "_T/config", cfg);

  cfg = String("{");
  cfg += "\"device_class\": \"humidity\"";
  cfg += ",\"name\": \"" + readID() + "_H\"";
  cfg += ",\"unique_id\": \"" + readID() + "_H\"";
  cfg += ",\"state_topic\": \"homeassistant/sensor/" + readID() + "/state\"";
  cfg += ",\"unit_of_measurement\": \"%\"";
  cfg += ",\"value_template\": \"{{ value_json.humidity}}\"";
  cfg += "}";

  Serial.println(cfg);
  sendmqtt("/" + readID() + "_H/config", cfg);

  led_timer.detach();
  digitalWrite(LED, LEDON); //灯常亮，表示连接成功
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
}

void callback(String payload_string) {
  Serial.println("receive:" + payload_string);

  if (payload_string == "stat") {
    sendStatus = true;
  }
  else if (payload_string == "reset") {
    blinkLED(LED, 400, 4);
    ESP.restart();
  }
  //  if (payload_string == "ip") {
  //    String path = MQTT_TOPIC + "/ip";
  //    mqttClient.publish(path.c_str(), currentIP.c_str());
  //  }
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

  wifiloop();

  if (times >= 100) {
    times = 0;
    //每秒读一次，不能放timer中，会挂
    float h = -1000;
    while (isnan(h) || h == -1000) {
      h = dht.readHumidity();
      delay(1);
    }

    float t = -1000;
    while (isnan(t) || t == -1000) {
      t = dht.readTemperature();
      delay(1);
    }

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
    dtostrf(oldt, 6, 2, celsiusTemp);
    dtostrf(oldh, 6, 2, humidityTemp);

    String dt = String("{");
    dt += "\"temperature\": \"" + String(celsiusTemp) + "\"";
    dt += ",\"humidity\": \"" + String(humidityTemp) + "\"";
    dt += "}";

    sendmqtt("/" + readID() + "/state", dt);
    Serial.println("statsend . . . . . . . . . . . . . . . . . . ");
    sendStatus = false;
  }
}
