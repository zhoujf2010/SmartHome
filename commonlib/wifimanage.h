
#include <PubSubClient.h>


void startWifi();
void wifiloop();
void clearroom();
String readID();
String readmqttip();

void initMQTT(String MQTT_TOPIC,std::function<void(String str)> callback);
void sendmqtt(String path, String msg);
void connectMQTT();
void checkConnection();
