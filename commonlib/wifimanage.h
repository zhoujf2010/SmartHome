
#include <PubSubClient.h>



void setVersion(String version);
void setdevicetype(String type);

void startWifi();
void wifiloop();
void clearroom();
String readID();
String readmqttip();
String getIP();

void initMQTT(String MQTT_TOPIC,String subtopic,boolean ignorefirstmsg,std::function<void(String str)> callback);
void sendmqtt(String path, String msg);
void connectMQTT();
void checkConnection();
