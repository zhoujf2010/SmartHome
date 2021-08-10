#include <Ticker.h>
#include "src/commonlib/wifimanage.h"
#include "src/commonlib/otatool.h"
#include "src/commonlib/common.h"
#include <EEPROM.h>



//易微联设备
String firmversion =    "2.0";
String DEVICE      =    "switch";
#define BUTTON          0
#define BUTTON1         9
#define BUTTON2         10
#define RELAY           12
#define RELAY1          5
#define RELAY2          4
#define LED             13
#define LEDON           LOW
#define LEDOFF          HIGH


Ticker btn_timer;
Ticker led_timer;

unsigned long count = 0;                                     // (Do not Change)
unsigned long count1 = 0;                                     // (Do not Change)
unsigned long count2 = 0;                                     // (Do not Change)
bool sendStatus = false;                                     // (Do not Change)
bool sendStatus1 = false;                                     // (Do not Change)
bool sendStatus2 = false;                                     // (Do not Change)
bool requestRestart = false;                                 // (Do not Change)

String MQTT_TOPIC = "";

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

  if (DEVICE == "orvibo")  {
    pinMode(4, OUTPUT);
    digitalWrite(4, LOW); //需把绿灯关了，否则红灯也不亮
  }

  //设置IO口模式
  pinMode(BUTTON, INPUT);
  pinMode(BUTTON1, INPUT);
  pinMode(BUTTON2, INPUT);

  pinMode(LED, OUTPUT);
  pinMode(RELAY, OUTPUT);
  pinMode(RELAY1, OUTPUT);
  pinMode(RELAY2, OUTPUT);
  digitalWrite(LED, LEDOFF);

  //恢复上次开关状态
  digitalWrite(RELAY, readCusVal(0) == 1 ? HIGH : LOW);
  digitalWrite(RELAY1, readCusVal(1) == 1 ? HIGH : LOW);
  digitalWrite(RELAY2, readCusVal(2) == 1 ? HIGH : LOW);

  btn_timer.attach(0.05, button);
  led_timer.attach(0.5, blink);

  startWifi();  //连接网络信息
  initOTA(LED);// 初使化OTA模式

  led_timer.detach();
  led_timer.attach(0.2, blink);

  String MQTT_TOPIC = "home/" + DEVICE + "/" + readID();
  initMQTT(MQTT_TOPIC, callback);

  StartFinish();

  led_timer.detach();
  digitalWrite(LED, LEDON); //灯常亮，表示连接成功
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
}

unsigned long lastPress;
int presstimes = 0;
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

      presstimes ++; //记录3秒内连接压
      if ((millis() > lastPress + (3000)) || (millis() < lastPress)) {
        lastPress = millis();
        presstimes = 0;
      }
      if (presstimes >= 5) {
        Serial.println("\n\nSonoff Rebooting . . . . . . . . Please Wait");
        clearroom();
        blinkLED(LED, 400, 4);
        ESP.restart();
      }
    }
    count = 0;
  }


  if (!digitalRead(BUTTON1)) {
    count1++;
  }
  else {
    if (count1 > 1 && count1 <= 40) {
      digitalWrite(RELAY1, !digitalRead(RELAY1));
      sendStatus1 = true;
    }
    count1 = 0;
  }

  if (!digitalRead(BUTTON2)) {
    count2++;
  }
  else {
    if (count2 > 1 && count2 <= 40) {
      digitalWrite(RELAY2, !digitalRead(RELAY2));
      sendStatus2 = true;
    }
    count2 = 0;
  }
}

unsigned long checkLastTime;

void callback(String payload_string) {
  Serial.println("receive:" + payload_string);

  if (payload_string == "stat") {
  }
  else if (payload_string == "on") {
    digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
    digitalWrite(RELAY, HIGH);
    writeCusVal(0, 1);
  }
  else if (payload_string == "off") {
    digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
    digitalWrite(RELAY, LOW);
    writeCusVal(0, 0);
  }
  else if (payload_string == "on1") {
    digitalWrite(RELAY1, HIGH);
    writeCusVal(1, 1);
  }
  else if (payload_string == "off1") {
    digitalWrite(RELAY1, LOW);
    writeCusVal(1, 0);
  }
  else if (payload_string == "on2") {
    digitalWrite(RELAY2, HIGH);
    writeCusVal(2, 1);
  }
  else if (payload_string == "off2") {
    digitalWrite(RELAY2, LOW);
    writeCusVal(2, 0);
  }
  else if (payload_string == "reset") {
    blinkLED(LED, 400, 4);
    ESP.restart();
  }
  sendStatus = true;
}


void loop() {
  if (loopOTA())
    return ;
  wifiloop();

  if (sendStatus) { //发送至mq
    if (digitalRead(RELAY) == HIGH)  {
      sendmqtt("/stat", "on");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . ON");
      writeCusVal(0, 1);

    } else {
      sendmqtt("/stat", "off");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . OFF");
      writeCusVal(0, 0);
    }
    sendStatus = false;
  }
  if (sendStatus1) { //发送至mq
    if (digitalRead(RELAY1) == HIGH)  {
      sendmqtt("/stat", "on1");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . ON1");
      writeCusVal(1, 1);
    } else {
      sendmqtt("/stat", "off1");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . OFF1");
      writeCusVal(1, 0);
    }
    sendStatus1 = false;
  }
  if (sendStatus2) { //发送至mq
    if (digitalRead(RELAY2) == HIGH)  {
      sendmqtt("/stat", "on2");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . ON2");
      writeCusVal(2, 1);
    } else {
      sendmqtt("/stat", "off2");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . OFF2");
      writeCusVal(2, 0);
    }
    sendStatus2 = false;
  }
}
