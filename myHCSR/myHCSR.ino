#include <Ticker.h>
#include "src/commonlib/wifimanage.h"
#include "src/commonlib/otatool.h"
#include "src/commonlib/common.h"

//人本传感器

String firmversion =    "2.0";
String DEVICE      =    "myhcsr";

#define LED            2
#define PIN          0
#define LEDON           LOW
#define LEDOFF          HIGH


Ticker btn_timer;
Ticker led_timer;

unsigned long count = 0;                                     // (Do not Change)
bool sendStatus = false;                                     // (Do not Change)
bool requestRestart = false;                                 // (Do not Change)

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

  //读取输入信息号
  pinMode(PIN, INPUT);
  btn_timer.attach(0.05, button);
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
}


int oldstat = -1;

//按钮处理
void button() {
  int newstat = digitalRead(PIN);
  if (newstat != oldstat){ //有变化发送至mq
      sendStatus = true;

      if (newstat == HIGH)
        digitalWrite(LED, LEDON); //亮起
      else
        digitalWrite(LED, LEDOFF); //亮起
  }
  oldstat = newstat;
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
  if (payload_string == "ip") {
      //sendmqtt("/ip",currentIP);
  }
}


void loop() {
  if (loopOTA())
    return ;
  wifiloop();

  if (sendStatus) { //发送至mq
    if (digitalRead(PIN) == HIGH)  {
      sendmqtt("/stat", "1");
      Serial.println("statchange . . . . . . . . . . . . . . . . . . 1");
    } else {
      sendmqtt("/stat", "0");
      Serial.println("statchange . . . . . . . . . . . . . . . . . . 0");
    }
    sendStatus = false;
  }
}
