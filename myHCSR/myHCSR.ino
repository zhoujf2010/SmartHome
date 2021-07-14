#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <EEPROM.h>
#include <Ticker.h>
#include <PubSubClient.h>
#include "otatool.h"
#include "wifimanage.h"


//人本传感器

String DEVICE    =      "myhcsr";
#define LED            2
#define PIN          0
#define LEDON           LOW
#define LEDOFF          HIGH


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


void setup()
{
  Serial.begin(115200);
  EEPROM.begin(512);
  Serial.println();
  int ch = EEPROM.read(225); //resetTimes
  Serial.print("ReadResetTimes:");
  Serial.println(ch);
  if (ch > 5 ) {
    clearroom();
  }
  EEPROM.write(225, EEPROM.read(225) + 1);
  EEPROM.commit();

  pinMode(LED, OUTPUT);
  pinMode(PIN, INPUT);
  btn_timer.attach(0.05, button);
  led_timer.attach(0.5, blink);

  startWifi();  //连接网络信息
  initOTA();// 初使化OTA模式
  led_timer.detach();
  led_timer.attach(0.2, blink);
  EEPROM.write(225, 0); //启动成功，清空次数
  EEPROM.commit();

  if (readmqttip() != "") {
    char* c = new char[200];  //深度copy一下，否则直接用就不行
    strcpy(c, readmqttip().c_str());
    mqttClient.setServer(c, 1883);
    mqttClient.setCallback(callback);
    connectMQTT();
    hasmqtt = true;
  }
  
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
  int newstat = digitalRead(PIN);
  if (newstat != oldstat){ //有变化发送至mq
      sendStatus = true;

//      if (newstat == HIGH)
//        digitalWrite(LED, LEDON); //亮起
//      else
//        digitalWrite(LED, LEDOFF); //亮起
  }
  oldstat = newstat;

  
  
//  if (!digitalRead(PIN)) {
//    count++;
//    if (count > 100) {//长按5秒
//      digitalWrite(LED, LEDON); //亮起
//    }
//  }
//  else {
//    if (count > 1 && count <= 40) {
//      digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
//      digitalWrite(RELAY, !digitalRead(RELAY));
//      sendStatus = true;
//    }
//    count = 0;
//  }
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


void callback(char* topic, byte* payload, unsigned int length) {
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


void loop() {
  if (loopOTA())
    return ;

  timedTasks();

  wifiloop();

  if (hasmqtt && !mqttClient.connected()) {
    connectMQTT();
  }
  
  if (sendStatus) { //发送至mq
    String path = MQTT_TOPIC + "/stat";
    if (digitalRead(PIN) == HIGH)  {
      mqttClient.publish(path.c_str(), "1");
      Serial.println("statchange . . . . . . . . . . . . . . . . . . 1");
    } else {
      mqttClient.publish(path.c_str(), "0");
      Serial.println("statchange . . . . . . . . . . . . . . . . . . 0");
    }
    sendStatus = false;
  }

  mqttClient.loop();
}
