
#include "src/commonlib/wifimanage.h"
#include "src/commonlib/otatool.h"
#include "src/commonlib/common.h"
#include "src/commonlib/wifimanage.h"
#include <PubSubClient.h>
#include<SoftwareSerial.h>


String DEVICE    =      "myirdev";
#define LED            13
#define LED2            12
#define SENDPIN         14
#define RECPIN          5
#define LEDON           LOW
#define LEDOFF          HIGH

//新建一个softSerial对象，rx:6,tx:5
SoftwareSerial softSerial1(0, 2);


void setup() {
  Serial.begin(115200);
  Serial.println("start......");

  //初始化软串口通信；
  softSerial1.begin(115200);
  //监听软串口通信
  softSerial1.listen();

  int ch = StartInit();
  Serial.print("ReadResetTimes:");
  Serial.println(ch);
  if (ch > 5 ) {
    StartError();
  }
  startWifi();  //连接网络信息
  initOTA(LED);// 初使化OTA模式

  //  if (readmqttip() != "") {
  //    char* c = new char[200];  //深度copy一下，否则直接用就不行
  //    strcpy(c, readmqttip().c_str());
  //    mqttClient.setServer(c, 1883);
  //    mqttClient.setCallback(callback);
  //    connectMQTT();
  //    hasmqtt = true;
  //  }

  StartFinish();
}


String getReceiveData(byte* buf, int len) {
  if (len > 5) {
    if (buf[0] == 0xff && buf[1] == 0x55) { //数据进来
      byte tp = buf[3];  //获取数据类型
      byte len = buf[4];

      String payload_string = "";
      for (int i = 0; i < len; ++i)
        payload_string += char(buf[i + 5]);
      return payload_string;
    }
  }
  return "";
}

byte bufx[255];
void Send(String data) {
  bufx[0] = 0xff;
  bufx[1] = 0x55;
  bufx[2] = 0;
  bufx[3] = 3;
  bufx[4] = data.length();
  for (int i = 0; i < bufx[4]; i ++) {
    bufx[i + 5] = data.c_str()[i];
  }


  for (int i = 0; i < bufx[4] + 5; i ++) {
    softSerial1.write(bufx[i]);
  }
}

byte buf[255];
void loop() {
  if (loopOTA())
    return ;

  //timedTasks();

  wifiloop();

  //读取从设备A传入的数据，并在串口监视器中显示

  int len = 0;
  while (softSerial1.available() > 0)
  {
    buf[len] = softSerial1.read();
    len++;
  }
  String recstr = getReceiveData(buf, len);

  if (recstr != "") {
    Serial.println("receive:" + recstr);

    if (recstr == "Hello") {
      Serial.println("check OK");
      Send("Hixxxx{\"aa\"}");
    }
    if (recstr == "ttttzzz") {
      Serial.println("check2 OK");
      Send("abc");
    }
  }
}
