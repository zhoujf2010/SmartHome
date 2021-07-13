
#include <ESP8266WiFi.h>
#include <EEPROM.h>
#include "src/commonlib/wifimanage.h"


#include "src/commonlib/otatool.h"

String DEVICE    =      "myirdev";
#define LED            13
#define LED2            12
#define SENDPIN         14
#define RECPIN          5
#define LEDON           LOW
#define LEDOFF          HIGH

#include<SoftwareSerial.h>
//新建一个softSerial对象，rx:6,tx:5
SoftwareSerial softSerial1(0,2);


void setup() {
  Serial.begin(115200);
  EEPROM.begin(512);
  Serial.println();
  
  //初始化软串口通信；
  softSerial1.begin(115200);
  //监听软串口通信
  softSerial1.listen();


  int ch = EEPROM.read(225); //resetTimes
  Serial.print("ReadResetTimes:");
  Serial.println(ch);
  if (ch > 5 ) {
    clearroom();
  }
  EEPROM.write(225, EEPROM.read(225) + 1);
  EEPROM.commit();
  startWifi();  //连接网络信息
  initOTA(LED);// 初使化OTA模式

}

void loop() {
  if (loopOTA())
    return ;

  //timedTasks();

  wifiloop();

  //读取从设备A传入的数据，并在串口监视器中显示
  
  if(softSerial1.available()>0)
  {
   Serial.write(softSerial1.read());
  }
}
