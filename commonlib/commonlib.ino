
#include "wifimanage.h"
#include "otatool.h"
#include "common.h"
#include <PubSubClient.h>

#define LED             13

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
bool hasmqtt = false;

String DEVICE    =      "sonoff";
String MQTT_TOPIC = "";


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

  if (readmqttip() != "") {
    char* c = new char[200];  //深度copy一下，否则直接用就不行
    strcpy(c, readmqttip().c_str());
    mqttClient.setServer(c, 1883);
    mqttClient.setCallback(callback);
    connectMQTT();
    hasmqtt = true;
  }


  StartFinish();

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

void checkConnection() {
  if (WiFi.status() != WL_CONNECTED) {
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



void callback(char* topic, byte* payload, unsigned int length) {
  String payload_string = "";
  for (int i = 0; i < length; ++i)
    payload_string += char(payload[i]);
  Serial.println("receive:" + payload_string);

}


void loop() {
  if (loopOTA())
    return ;

  timedTasks();

  wifiloop();


  if (hasmqtt && !mqttClient.connected()) {
    connectMQTT();
  }

  String path = MQTT_TOPIC + "/stat";
  mqttClient.publish(path.c_str(), "on");
  Serial.println("Relay . . . . . . . . . . . . . . . . . . ON");
}
