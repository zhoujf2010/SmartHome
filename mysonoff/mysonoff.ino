#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <EEPROM.h>
#include <Ticker.h>
#include <ArduinoOTA.h>
#include <PubSubClient.h>
#include "wifimanage.h"


//易微联设备
String DEVICE    =      "sonoff";
#define BUTTON          0
#define RELAY           12
#define LED             13
#define LEDON           LOW
#define LEDOFF          HIGH


//// 欧瑞博设备
//String DEVICE    =      "orvibo";
//#define BUTTON          14
//#define RELAY           5
//#define LED             12
//#define LEDON           HIGH
//#define LEDOFF          LOW

////8266测试芯片
//String DEVICE    =      "8266";
//#define BUTTON          0
//#define RELAY           2 //暂时引脚，随便放个
//#define LED             2
//#define LEDON           HIGH
//#define LEDOFF          LOW


Ticker btn_timer;
Ticker led_timer;

unsigned long count = 0;                                     // (Do not Change)
bool OTAupdate = false;
bool sendStatus = false;                                     // (Do not Change)
bool requestRestart = false;                                 // (Do not Change)
bool hasmqtt = false;

String MQTT_TOPIC = "";

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);


void setup()
{
  Serial.begin(115200);
  EEPROM.begin(512);
  Serial.println();

  pinMode(LED, OUTPUT);
  pinMode(RELAY, OUTPUT);
  pinMode(BUTTON, INPUT);
  digitalWrite(LED, LEDOFF);
  digitalWrite(RELAY, LOW);

  if (DEVICE == "orvibo")  {
    pinMode(4, OUTPUT);
    digitalWrite(4, LOW); //需把绿灯关了，否则红灯也不亮
  }

  btn_timer.attach(0.05, button);
  led_timer.attach(0.5, blink);

  startWifi();  //连接网络信息
  initOTA();// 初使化OTA模式
  led_timer.detach();
  led_timer.attach(0.2, blink);

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

void initOTA() {
  ArduinoOTA.onStart([]() {
    OTAupdate = true;
    blinkLED(LED, 400, 2);
    digitalWrite(LED, LEDON);
    Serial.println("OTA Update Initiated . . .");
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nOTA Update Ended . . .s");
    ESP.restart();
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    digitalWrite(LED, LEDOFF);
    delay(5);
    digitalWrite(LED, LEDON);
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    blinkLED(LED, 40, 2);
    OTAupdate = false;
    Serial.printf("OTA Error [%u] ", error);
    if (error == OTA_AUTH_ERROR) Serial.println(". . . . . . . . . . . . . . . Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println(". . . . . . . . . . . . . . . Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println(". . . . . . . . . . . . . . . Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println(". . . . . . . . . . . . . . . Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println(". . . . . . . . . . . . . . . End Failed");
  });
  ArduinoOTA.setHostname(readID().c_str());
  ArduinoOTA.begin();
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
}

void blinkLED(int pin, int duration, int n) {
  for (int i = 0; i < n; i++)  {
    digitalWrite(pin, LEDON);
    delay(duration);
    digitalWrite(pin, LEDOFF);
    delay(duration);
  }
}

//按钮处理
void button() {
  if (!digitalRead(BUTTON)) {
    count++;
    if (count > 100) {//长按5秒
      digitalWrite(LED, LEDON); //亮起
    }
  }
  else {
    if (count > 1 && count <= 40) {
      digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
      digitalWrite(RELAY, !digitalRead(RELAY));
      sendStatus = true;
    }
    else if (count > 100) {
      Serial.println("\n\nSonoff Rebooting . . . . . . . . Please Wait");
      clearroom();
      blinkLED(LED, 400, 4);
      ESP.restart();
    }
    count = 0;
  }
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
  }
  else if (payload_string == "on") {
    digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
    digitalWrite(RELAY, HIGH);
  }
  else if (payload_string == "off") {
    digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
    digitalWrite(RELAY, LOW);
  }
  else if (payload_string == "reset") {
    blinkLED(LED, 400, 4);
    ESP.restart();
  }
  sendStatus = true;
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
  if (WiFi.status() != WL_CONNECTED){
    ESP.restart();
  }
  //  if (WiFi.status() == WL_CONNECTED)  {
  //    if (mqttClient.connected()) {
  //      Serial.println("mqtt broker connection . . . . . . . . . . OK");
  //    }
  //    else {
  //      Serial.println("mqtt broker connection . . . . . . . . . . LOST");
  //      requestRestart = true;
  //    }
  //  }
  //  else {
  //    Serial.println("WiFi connection . . . . . . . . . . LOST");
  //    requestRestart = true;
  //  }

//  if (!mqttClient.connected()) {
//    //    if (!isconnecting) {
//    //      isconnecting = true;
//    //      Serial.println("start connect mqtt");
//    //      mqtt_timer.once(0.1, reconnect);
//    //      mqtt_timer.detach();
//    //    }
//
//    Serial.print("Attempting MQTT connection...");
//    if (mqttClient.connect(readID().c_str())) {
//      Serial.println("connected");
//      mqttClient.subscribe(MQTT_TOPIC);
//    } else {
//      Serial.print("failed, rc=");
//      Serial.print(mqttClient.state());
//      Serial.println(" try again in 5 seconds");
//      // Wait 5 seconds before retrying
////      delay(5000);
//    }
//  }
}


void loop() {
  ArduinoOTA.handle();
  if (OTAupdate)
    return ;

  timedTasks();
  
  wifiloop();

  if (hasmqtt && !mqttClient.connected()) {
    connectMQTT();
  }

  if (sendStatus) { //发送至mq
    String path = MQTT_TOPIC + "/stat";
    if (digitalRead(RELAY) == HIGH)  {
      mqttClient.publish(path.c_str(), "on");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . ON");
    } else {
      mqttClient.publish(path.c_str(), "off");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . OFF");
    }
    sendStatus = false;
  }
  mqttClient.loop();
}
