#include "src/commonlib/wifimanage.h"
#include "src/commonlib/otatool.h"
#include "src/commonlib/common.h"
#include <Ticker.h>


//光线传感器

String firmversion =    "2.2";
String DEVICE    =      "mylightsensor";
#define LED             2
#define PIN             0
#define LEDON           LOW
#define LEDOFF          HIGH


Ticker btn_timer;
Ticker led_timer;

bool sendStatus = false;                                     // (Do not Change)

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

  pinMode(PIN, INPUT);
  btn_timer.attach(0.05, button);
  led_timer.attach(0.5, blink);


  startWifi();  //连接网络信息
  initOTA(LED);// 初使化OTA模式

  String MQTT_TOPIC = "homeassistant/binary_sensor/" + readID();
  initMQTT(MQTT_TOPIC, "/set", false, callback);

  StartFinish();

  String cfg = String("{");
  cfg += "\"device_class\": \"light\"";
  cfg += ",\"name\": \"" + readID() + "\"";
  cfg += ",\"unique_id\": \"" + readID() + "\"";
  cfg += ",\"state_topic\": \"homeassistant/binary_sensor/" + readID() + "/state\"";
  cfg += "}";

  Serial.println(cfg);
  sendmqtt("/config", cfg);

  led_timer.detach();
  digitalWrite(LED, LEDON); //灯常亮，表示连接成功
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
}

int oldstat = -1;

//按钮处理
void button() {
  int newstat = digitalRead(PIN);
  if (newstat != oldstat) { //有变化发送至mq
    sendStatus = true;
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
  //  if (payload_string == "ip") {
  //    String path = MQTT_TOPIC + "/ip";
  //    mqttClient.publish(path.c_str(), currentIP.c_str());
  //  }
}

void loop() {
  if (loopOTA())
    return ;

  wifiloop();

  if (sendStatus) { //发送至mq
    if (digitalRead(PIN) == HIGH)  { //无光
      sendmqtt("/state", "OFF");
      Serial.println("statchange . . . . . . . . . . . . . . . . . . 1");
      digitalWrite(LED, LEDON);
    } else { //有光
      sendmqtt("/state", "ON");
      Serial.println("statchange . . . . . . . . . . . . . . . . . . 0");
      digitalWrite(LED, LEDOFF);
    }
    sendStatus = false;
  }
}
