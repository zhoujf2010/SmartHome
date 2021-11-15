
#include "src/commonlib/wifimanage.h"
#include "src/commonlib/otatool.h"
#include "src/commonlib/common.h"
#include "src/commonlib/wifimanage.h"
#include <PubSubClient.h>
#include<SoftwareSerial.h>
#include <Ticker.h>
#include <ArduinoJson.h>
#include <WebSocketsClient.h>
#include <Hash.h>

String firmversion =    "2.0";
String DEVICE    =      "bridgeLCD";
#define LED            2
#define LEDON           LOW
#define LEDOFF          HIGH

WebSocketsClient webSocket;

Ticker led_timer;

void setup() {
  Serial.begin(115200);
  Serial.println("start......");
  setVersion(firmversion);
  setdevicetype(DEVICE);

  pinMode(LED, OUTPUT);
  led_timer.attach(0.5, blink);

  int ch = StartInit();
  Serial.print("ReadResetTimes:");
  Serial.println(ch);
  if (ch > 5 ) {
    StartError();
  }
  startWifi();  //连接网络信息
  initOTA(LED);// 初使化OTA模式

  String mqttip = readmqttip();
  if (mqttip != "") {
    webSocket.begin(mqttip, 8123, "/api/websocket");
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(5000); // 每5秒，check一下连接
    webSocket.enableHeartbeat(15000, 3000, 2); //每15000ms执行一次ping，3000ms内期望得到pong，2次未满足，连接判为断开
  }

  led_timer.detach();
  digitalWrite(LED, LEDON); //灯常亮，表示连接成功

  StartFinish();
}

//void sendPing(){
//  
//}
void blink() {
  digitalWrite(LED, !digitalRead(LED));
}

String token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiIyMzhiNTU4ZTkzNGY0YjA3OWQ5MWM1ODU4NzJlYTYzNSIsImlhdCI6MTYzNjQ2NTIwOSwiZXhwIjoxOTUxODI1MjA5fQ.bh_Yu8h0BLw3Ur7CDlknzp7Z7tya0wLuG3TGIGpvkBA";

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_DISCONNECTED:
      Serial.printf("[WSc] Disconnected!\n");
      break;
    case WStype_CONNECTED: {
        Serial.printf("[WSc] Connected to url: %s\n", payload);
        // send message to server when Connected
        String ss = "{\"id\":1,\"type\": \"auth\", \"access_token\":\"" + token + "\"}";
        webSocket.sendTXT(ss);
      }
      break;
    case WStype_TEXT: {
        Serial.printf("[WSc] get text: %s\n", payload);
        String ttt = (char*)payload;
        if (ttt.indexOf("auth_ok") > 0)
        {
          String ss = "{\"id\":1,\"type\": \"subscribe_events\"}";
          webSocket.sendTXT(ss);
        }
        else
          Receive_command(ttt);
      }
      // send message to server
      // webSocket.sendTXT("message here");
      break;
    case WStype_PONG:
      // answer to a ping we send
      Serial.printf("[WSc] get pong\n");
      break;
  }
}


StaticJsonDocument<200> doc;

void Receive_command(String str){
  
}

long msg_id = 0;
void SendtoHass(String str) {
  msg_id += 1;
  if (msg_id > 9999999)
    msg_id = 1;
    
  doc.clear();
  // Deserialize the JSON document
  DeserializationError error = deserializeJson(doc, str.c_str());
  // Test if parsing succeeds.
  if (error) {
    Serial.println(error.f_str());
    return "deserializeJson() failed: ";
  }
  const char* type = doc["type"];
  const char* msgx = doc["msg"];
  
    
  //   self._last_msg_id += 1
  //        message_id = message["id"] = self._last_msg_id
}

int pos = 0;

byte getCheckSum(byte *pData, int len) {
  int sum = 0;
  for (int i = 0; i < len; ++i) {
    sum += pData[i];
  }

  return (byte) (~sum + 1);
}

String getReceiveData(byte* buf) {
  if (pos <= 5 )
    return ""; //数据不足

  if (buf[0] != 0xff || buf[1] != 0x55) { //不是指定数据格式，重读
    pos = 0;
    Serial.println("ReRead");
    return "";
  }
  byte tp = buf[3];  //获取数据类型
  byte datalen = buf[4];
  if (pos < datalen + 5) {
    Serial.println("Less");
    return ""; //数据长度不足
  }

  if (getCheckSum(buf, pos - 1) != buf[pos - 1]) { //数据验证不对，数据抛弃
    Serial.println("CheckError");
    Serial.println(getCheckSum(buf, pos - 1) );
    Serial.println(buf[pos - 1] );
    pos = 0;
    return "";
  }

  String payload_string = "";
  for (int i = 0; i < datalen; ++i)
    payload_string += char(buf[i + 5]);

  pos = 0;//正确读到数据，游标归位
  return payload_string;
}

byte bufx[255];
void SendtoLCD(byte* data, int len) {
  bufx[0] = 0xff;
  bufx[1] = 0x55;
  bufx[2] = 0;
  bufx[3] = 0;
  bufx[4] = len;
  for (int i = 0; i < len; i ++) {
    bufx[i + 5] = data[i];
  }
  bufx[len + 5] = getCheckSum(bufx, len + 5);

  for (int i = 0; i < len + 6; i ++) {
    Serial.write(bufx[i]);
  }
}


String recDeal(String msg) {
  doc.clear();
  // Deserialize the JSON document
  DeserializationError error = deserializeJson(doc, msg.c_str());
  // Test if parsing succeeds.
  if (error) {
    Serial.println(error.f_str());
    return "deserializeJson() failed: ";
  }
  const char* type = doc["type"];
  const char* msgx = doc["msg"];
  String s_type = String(type);
  if (s_type != "inner")
    return "";
  String s_msg = String(msgx);
  String retstr = "";
  if (s_msg == "ip")
    retstr = getIP();
  else if (s_msg == "reset") {
    ESP.restart();
    retstr = "OK";
  }
  else if (s_msg == "clear") {
    clearroom();
    ESP.restart();
    retstr = "OK";
  }
  else
    retstr = "unknow cmd";


  String result = "{\"type\":\"inner\",\"msg\":\"" + s_msg + "\",\"result\":\"" + retstr + "\"}";
  return result;
}

byte buf[255];
byte buf2[255];
void loop() {
  if (loopOTA())
    return ;

  wifiloop();
  webSocket.loop();

    //读取从设备A传入的数据，并在串口监视器中显示
    while (Serial.available() > 0)
    {
      buf[pos] = Serial.read();
      pos++;
    }
    String recstr = getReceiveData(buf);
  
  //  if (recstr != "") {
  //    softSerial1.println("receive from lcd:" + recstr);
  //
  //    //内部命令，发给ESP的，直接处理，并返回
  //    String tmp = recDeal(recstr);
  //    if (tmp != "")
  //      SendtoLCD((byte*)tmp.c_str(), tmp.length());
  //
  ////    if (serverClient && serverClient.connected()) {
  ////      serverClient.write(recstr.c_str(), recstr.length());
  ////    }
  //  }

  //  //从网络读取，写入LCD
  //  if (sockertserver.hasClient())
  //  {
  //    if (!serverClient || !serverClient.connected()) {
  //      if (serverClient)
  //        serverClient.stop();//未联接,就释放
  //      serverClient = sockertserver.available();//分配新的
  //    }
  //    WiFiClient serverClient = sockertserver.available();
  //    serverClient.stop();  //关闭后面接入
  //  }
  //
  //  if (serverClient && serverClient.connected())
  //  {
  //    int p = 0;
  //    while (serverClient.available()) {
  //      char c = serverClient.read();
  //      buf2[p] = c;
  //      p++;
  //      if (p >= 255)
  //        p = 0;
  //    }
  //
  //    if (p > 0) {
  //      SendtoLCD(buf2, p);
  ////    uint32_t free = system_get_free_heap_size(); // get free ram
  ////    Serial.println(free); // output ram to serial
  //    }
  //  }

//  delay(5);
}
