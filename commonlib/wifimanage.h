#pragma once // Important if you include header files from other header files

#include <PubSubClient.h>
#include <ESP8266WebServer.h>



void setVersion(String version);
void setdevicetype(String type);

ESP8266WebServer* startWifi();
void wifiloop();
void clearroom();
String readID();
String readmqttip();
String getIP();

void initMQTT(String MQTT_TOPIC,String subtopic,boolean ignorefirstmsg,std::function<void(String topic,String payload)> callback, std::function<void()> initDevice);
void sendmqtt(String path, String msg);
void connectMQTT();
void checkConnection();
