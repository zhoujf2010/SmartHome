
#include "wifimanage.h"
#include "otatool.h"
#include "common.h"

#define LED             13


String DEVICE    =      "sonoff";


void setup() {
  Serial.begin(115200);
  Serial.println("start......");

  int ch = StartInit();
  Serial.print("ReadResetTimes:");
  Serial.println(ch);
  if (ch > 5 ) {
    StartError();
  }
  startWifi();  //连接网络信息
  initOTA(LED);// 初使化OTA模式

  String MQTT_TOPIC = "home/" + DEVICE + "/" + readID();
  initMQTT(MQTT_TOPIC, callback);

  StartFinish();

}


void callback(String payload_string) {
  Serial.println("receive:" + payload_string);
}

void loop() {
  if (loopOTA())
    return ;
  wifiloop();

  sendmqtt("/stat", "on");
  Serial.println("Relay . . . . . . . . . . . . . . . . . . ON");
}
