#include <Ticker.h>
#include "wifimanage.h"
#include "otatool.h"
#include "common.h"

String firmversion =    "2.0";
String DEVICE      =    "common";

#define LED             2
#define LEDON           LOW
#define LEDOFF          HIGH


Ticker led_timer;


void setup() {
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

  String MQTT_TOPIC = "homeassistant/" + DEVICE + "/" + readID();
  initMQTT(MQTT_TOPIC, "/set",false, callback,initMqttDevice);
  
  StartFinish();

  led_timer.detach();
  digitalWrite(LED, LEDON); //灯常亮，表示连接成功
}

void initMqttDevice(){
  String cfg = String("{");
  cfg += "\"name\": \"" + readID() + "\"";
  cfg += ",\"unique_id\":\"" + readID() + "\"";
  //cfg += ",\"device_class\": \"light\"";
  cfg += ",\"command_topic\": \"homeassistant/" + DEVICE + "/" + readID() + "/set\"";
  cfg += ",\"state_topic\": \"homeassistant/" + DEVICE + "/" + readID() + "/state\"";
  cfg += "}";

  Serial.println(cfg);
  sendmqtt("/config", cfg);
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
}

Ticker btn_timer;
int BUTTON = -1;

void callback(String topic, String payload_string) {
  Serial.println("receive:" + payload_string);

  int v = payload_string.toInt();
  Serial.println("receive:" + v);

  byte cmd = v >> 6 ;  //头两个为命令类型
  byte param = (v & 0x30) >> 4; //高四位中后两位为命令参数
  char pin = v & 0x0F;  //低四位为pin编号

  Serial.println("cmd:" + String((int)cmd));
  Serial.println("param:" + String((int)param));
  Serial.println("pin:" + String((int)pin));

  if (cmd == 0) { //设置PIN类型
    if (param == 1)
      pinMode(pin, OUTPUT);
    else if (param == 2)
      pinMode(pin, INPUT);
    else if (param == 3)
      pinMode(pin, INPUT_PULLUP);
  }
  else if (cmd == 1) { //写值
    if (param == 0)
      digitalWrite(pin, LOW);
    else if (param == 1)
      digitalWrite(pin, HIGH);
  }
  else if (cmd == 2) {//读值
    if (BUTTON >=0){
      btn_timer.detach();
      BUTTON = -1;
    }
    else{
      BUTTON = pin;
      btn_timer.attach(0.05, button);
    }
  }
}

void button() {
  if (BUTTON < 0)
  return ;
  if (digitalRead(BUTTON))
      Serial.println("read:HIGH");
  else
      Serial.println("read:LOW");
}

void loop() {
  if (loopOTA())
    return ;
  wifiloop();

//  sendmqtt("/state", "on");
//  Serial.println("Relay . . . . . . . . . . . . . . . . . . ON");
}
