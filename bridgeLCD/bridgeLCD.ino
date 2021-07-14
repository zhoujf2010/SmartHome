
#include "src/commonlib/wifimanage.h"
#include "src/commonlib/otatool.h"
#include "src/commonlib/common.h"
#include "src/commonlib/wifimanage.h"
#include <PubSubClient.h>
#include<SoftwareSerial.h>
#include <Ticker.h>

WiFiServer sockertserver(8266);//你要的端口号，随意修改，范围0-65535
WiFiClient serverClient;

String DEVICE    =      "bridgeLCD";
#define LED            2
#define LEDON           LOW
#define LEDOFF          HIGH

//新建一个softSerial对象，rx:6,tx:5
SoftwareSerial softSerial1(0, 2);


Ticker led_timer;

void setup() {
  Serial.begin(115200);
  Serial.println("start......");

  //初始化软串口通信；
  softSerial1.begin(115200);
  //监听软串口通信
  softSerial1.listen();

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

  sockertserver.begin();
  sockertserver.setNoDelay(true);  //加上后才正常些

  led_timer.detach();
  digitalWrite(LED, LEDON); //灯常亮，表示连接成功

  StartFinish();
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
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

void Send(byte* data, int len) {
  bufx[0] = 0xff;
  bufx[1] = 0x55;
  bufx[2] = 0;
  bufx[3] = 3;
  bufx[4] = len;
  for (int i = 0; i < bufx[4]; i ++) {
    bufx[i + 5] = data[i];
  }

  for (int i = 0; i < bufx[4] + 5; i ++) {
    softSerial1.write(bufx[i]);
  }
}

byte buf[255];
byte buf2[255];
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
    Serial.println("receive from lcd:" + recstr);
    if (serverClient && serverClient.connected()) {
      serverClient.write(recstr.c_str(), recstr.length());
      Serial.println("send to seb:" + recstr);
    }

    //    if (recstr == "Hello") {
    //      Serial.println("check OK");
    //      Send("Hixxxx{\"aa\"}");
    //    }
    //    if (recstr == "ttttzzz") {
    //      Serial.println("check2 OK");
    //      Send("abc");
    //    }
  }

  uint8_t i;
  if (sockertserver.hasClient())
  {
    if (!serverClient || !serverClient.connected()) {
      if (serverClient)
        serverClient.stop();//未联接,就释放
      serverClient = sockertserver.available();//分配新的
    }
    WiFiClient serverClient = sockertserver.available();
    serverClient.stop();  //关闭后面接入
  }

  if (serverClient && serverClient.connected())
  {
    int p = 0;
    while (serverClient.available()) {
      char c = serverClient.read();
      Serial.print(c);
      buf2[p] = c;
      p++;
    }

    if (p > 0) {
      String payload_string = "";
      for (int i = 0; i < p; ++i)
        payload_string += char(buf2[i]);

      Send(buf2, p);
      Serial.println("receive from web:" + payload_string);
    }
  }
}
