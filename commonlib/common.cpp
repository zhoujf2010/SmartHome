
#include <EEPROM.h>
#include "common.h"
#include "Arduino.h"


void blinkLED(int pin, int duration, int n) {
  for (int i = 0; i < n; i++)  {
    digitalWrite(pin, LOW);
    delay(duration);
    digitalWrite(pin, HIGH);
    delay(duration);
  }
}


void clearroom() {
  for (int i = 0; i < 225; ++i) {
    EEPROM.write(i, 0);
  }
  EEPROM.write(225, 0);
  EEPROM.commit();
}

void StartError(){
  clearroom();  //清空保存的wifi用户名和密码
  ESP.restart();
}

void StartFinish(){
  
  EEPROM.write(225, 0);
  EEPROM.commit();
}


int StartInit(){
  EEPROM.begin(512);
  int ch = EEPROM.read(225); //resetTimes
  EEPROM.write(225, EEPROM.read(225) + 1);
  EEPROM.commit();
  return ch;
}
