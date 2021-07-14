
#include "otatool.h"


bool OTAupdate = false;

void initOTA() {
  ArduinoOTA.onStart([]() {
    OTAupdate = true;
    blinkLED(LED, 400, 2);
    digitalWrite(LED, LEDON);
    Serial.println("OTA Update Initiated . . .");
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nOTA Update Ended . . .s");
    ESP.restart();
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    digitalWrite(LED, LEDOFF);
    delay(5);
    digitalWrite(LED, LEDON);
    Serial.printf("Progress: %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t error) {
    blinkLED(LED, 40, 2);
    OTAupdate = false;
    Serial.printf("OTA Error [%u] ", error);
    if (error == OTA_AUTH_ERROR) Serial.println(". . . . . . . . . . . . . . . Auth Failed");
    else if (error == OTA_BEGIN_ERROR) Serial.println(". . . . . . . . . . . . . . . Begin Failed");
    else if (error == OTA_CONNECT_ERROR) Serial.println(". . . . . . . . . . . . . . . Connect Failed");
    else if (error == OTA_RECEIVE_ERROR) Serial.println(". . . . . . . . . . . . . . . Receive Failed");
    else if (error == OTA_END_ERROR) Serial.println(". . . . . . . . . . . . . . . End Failed");
  });
  ArduinoOTA.setHostname(readID().c_str());
  ArduinoOTA.begin();
}


boolean loopOTA(){
  ArduinoOTA.handle();
  return OTAupdate;  
}
