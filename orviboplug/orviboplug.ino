#include <Ticker.h>
#include "src/commonlib/wifimanage.h"
#include "src/commonlib/otatool.h"
#include "src/commonlib/common.h"
#include <EEPROM.h>


String firmversion =    "2.5";

// 欧瑞博设备
String DEVICE    =      "plug";
#define BUTTON          14
#define RELAY           5
#define LED             12
#define LEDON           HIGH
#define LEDOFF          LOW

Ticker btn_timer;
Ticker led_timer;

unsigned long count = 0;                                     // (Do not Change)
bool sendStatus = false;                                     // (Do not Change)
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

  //需把绿灯关了，否则红灯也不亮
  pinMode(4, OUTPUT);
  digitalWrite(4, LOW); 

  //设置IO口模式
  pinMode(BUTTON, INPUT);

  pinMode(LED, OUTPUT);
  pinMode(RELAY, OUTPUT);
  digitalWrite(LED, LEDOFF);

  //恢复上次开关状态
  digitalWrite(RELAY, readCusVal(0) == 1 ? HIGH : LOW);

  btn_timer.attach(0.05, button);
  led_timer.attach(0.5, blink);

  startWifi();  //连接网络信息
  initOTA(LED);// 初使化OTA模式

  led_timer.detach();
  led_timer.attach(0.2, blink);

  String MQTT_TOPIC = "homeassistant/" + String("switch") + "/" + readID();
  initMQTT(MQTT_TOPIC, "/set",false, callback,initMqttDevice);

  StartFinish();

  led_timer.detach();
  digitalWrite(LED, LEDON); //灯常亮，表示连接成功
}


void initMqttDevice(){
  String cfg = String("{");
  cfg += "\"name\": \"" + readID() + "\"";
  cfg += ",\"unique_id\":\"" + readID() + "\"";
  //cfg += ",\"device_class\": \"power\"";
  cfg += ",\"command_topic\": \"homeassistant/" + String("switch") + "/" + readID() + "/set\"";
  cfg += ",\"state_topic\": \"homeassistant/" + String("switch") + "/" + readID() + "/state\"";
  cfg += "}";

  Serial.println(cfg);
  Serial.println("222");
  sendmqtt("/config", cfg);
  Serial.println("333");
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
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

unsigned long checkLastTime;

void callback(String topic, String payload_string) {
  Serial.println("receive:" + payload_string);

  if (payload_string == "stat") {
  }
  else if (payload_string == "ON") {
    digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
    digitalWrite(RELAY, HIGH);
    writeCusVal(0, 1);
  }
  else if (payload_string == "OFF") {
    digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
    digitalWrite(RELAY, LOW);
    writeCusVal(0, 0);
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
      sendmqtt("/state", "ON");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . ON");
      writeCusVal(0, 1);

    } else {
      sendmqtt("/state", "OFF");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . OFF");
      writeCusVal(0, 0);
    }
    sendStatus = false;
  }
}
