
#include <Ticker.h>
#include <PubSubClient.h>
#include "src/commonlib/wifimanage.h"
#include "src/commonlib/otatool.h"
#include "src/commonlib/common.h"
#include "src/commonlib/wifimanage.h"
#include "IRTool.h"


//红外线遥控器

String firmversion =    "2.0";
String DEVICE    =      "irdev";
#define LED            13
#define LED2            12
#define SENDPIN         14
#define RECPIN          5
#define LEDON           LOW
#define LEDOFF          HIGH

Ticker led_timer;

unsigned long count = 0;                                     // (Do not Change)
bool sendStatus = false;                                     // (Do not Change)
bool requestRestart = false;                                 // (Do not Change)

IRrecv irrecv(RECPIN);
IRsend irsend(SENDPIN);
decode_results results;
boolean isfirstconnMQTT = false;
const char* kCommandDelimiter = ",";
const char* kSequenceDelimiter = ";";
const char kPauseChar = 'P';

void setup()
{
  Serial.begin(115200);
  Serial.println("start......");
  setVersion(firmversion);
  setdevicetype(DEVICE);
    
  int ch = StartInit();
  Serial.print("ReadResetTimes:");
  Serial.println(ch);
  if (ch > 5 ) {
    StartError();
  }

  pinMode(LED, OUTPUT);
  pinMode(LED2, OUTPUT);
  digitalWrite(LED2, LEDOFF);

  led_timer.attach(0.5, blink);

  startWifi();  //连接网络信息
  initOTA(LED);// 初使化OTA模式
  led_timer.detach();
  led_timer.attach(0.2, blink);
  
  String MQTT_TOPIC = "home/" + DEVICE + "/" + readID();
  initMQTT(MQTT_TOPIC, callback);

  //启动红外
  irrecv.enableIRIn();
  irsend.begin();

  led_timer.detach();
  digitalWrite(LED, LEDON); //灯常亮，表示连接成功
  
  StartFinish();
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
}


// Arduino framework doesn't support strtoull(), so make our own one.
uint64_t getUInt64fromHex(char const *str) {
  uint64_t result = 0;
  uint16_t offset = 0;
  // Skip any leading '0x' or '0X' prefix.
  if (str[0] == '0' && (str[1] == 'x' || str[1] == 'X')) offset = 2;
  for (; isxdigit((unsigned char)str[offset]); offset++) {
    char c = str[offset];
    result *= 16;
    if (isdigit(c))
      result += c - '0';  // '0' .. '9'
    else if (isupper(c))
      result += c - 'A' + 10;  // 'A' .. 'F'
    else
      result += c - 'a' + 10;  // 'a' .. 'f'
  }
  return result;
}

const int32_t kMaxPauseMs = 10000;  // 10 Seconds.
bool lastSendSucceeded = false;  // Store the success status of the last send.

void callback(String payload_string) {
//  if (isfirstconnMQTT)  { //跳过首次收到的信息
//    isfirstconnMQTT = false;
//    return ;
//  }

  Serial.print("receive:" + payload_string + "   ");
  //  uint64_t number = getUInt64fromHex(payload_string.c_str());
  //  serialPrintUint64(number, HEX);
  //  Serial.println("");//"receive:" + number);
  //  irsend.sendNEC(number);

  // Make a copy of the callback string as strtok destroys it.
  char* callback_c_str = strdup(payload_string.c_str());
  debug("MQTT Payload (raw):");
  debug(callback_c_str);

  // Chop up the str into command chunks.
  // i.e. commands in a sequence are delimitered by ';'.
  char* sequence_tok_ptr;
  for (char* sequence_item = strtok_r(callback_c_str, kSequenceDelimiter,
                                      &sequence_tok_ptr);
       sequence_item != NULL;
       sequence_item = strtok_r(NULL, kSequenceDelimiter, &sequence_tok_ptr)) {
    // Now, process each command individually.
    char* tok_ptr;
    // Make a copy of the sequence_item str as strtok_r stomps on it.
    char* ircommand = strdup(sequence_item);
    // Check if it is a pause command.
    switch (ircommand[0]) {
      case kPauseChar:
        { // It's a pause. Everything after the 'P' should be a number.
          //          int32_t msecs = std::min((int32_t) strtoul(ircommand + 1, NULL, 10),
          //                                   kMaxPauseMs);
          //          delay(msecs);
          ////          mqtt_client.publish(MqttAck.c_str(),
          ////                              String(kPauseChar + String(msecs)).c_str());
          //          mqttSentCounter++;
          break;
        }
      default:  // It's an IR command.
        {
          // Get the numeric protocol type.
          decode_type_t ir_type = (decode_type_t)atoi(strtok_r(
                                    ircommand, kCommandDelimiter, &tok_ptr));
          char* next = strtok_r(NULL, kCommandDelimiter, &tok_ptr);
          // If there is unparsed string left, try to convert it assuming it's
          // hex.
          uint64_t code = 0;
          uint16_t nbits = 0;
          uint16_t repeat = 0;
          if (next != NULL) {
            code = getUInt64fromHex(next);
            next = strtok_r(NULL, kCommandDelimiter, &tok_ptr);
          } else {
            // We require at least two value in the string. Give up.
            break;
          }
          // If there is still string left, assume it is the bit size.
          if (next != NULL) {
            nbits = atoi(next);
            next = strtok_r(NULL, kCommandDelimiter, &tok_ptr);
          }
          // If there is still string left, assume it is the repeat count.
          if (next != NULL)
            repeat = atoi(next);
          // send received MQTT value by IR signal
          lastSendSucceeded = sendIRCode(
                                &irsend, ir_type, code,
                                strchr(sequence_item, kCommandDelimiter[0]) + 1, nbits, repeat);
        }
    }
    free(ircommand);
  }
  free(callback_c_str);






  digitalWrite(LED2, LEDON);
  delay(20);
  digitalWrite(LED2, LEDOFF);
}

const uint16_t kCaptureBufferSize = 1024;

const uint8_t kTolerancePercentage = kTolerance;  // kTolerance is normally 25%

void loop() {
  if (loopOTA())
    return ;

  wifiloop();
  
  if (irrecv.decode(&results)) {
    //String path = MQTT_TOPIC + "/receive";
    //
    //    uint64_t number = results.value;
    //    unsigned long long1 = (unsigned long)((number & 0xFFFF0000) >> 16 );
    //    unsigned long long2 = (unsigned long)((number & 0x0000FFFF));
    //    String seg1 = String(long2, HEX);
    //    while (seg1.length() < 4) {
    //      seg1 = "0" + seg1;
    //    }
    //    String hex = String(long1, HEX) + seg1; // six octets
    //    hex.toUpperCase();
    //    Serial.print("rec:");
    //    serialPrintUint64(results.value, HEX);
    //    Serial.print("  ");
    //    Serial.println(hex);
    //    mqttClient.publish(path.c_str(), hex.c_str());
    //
    //    irrecv.resume();  // Receive the next value

    //   // Display a crude timestamp.
    //      uint32_t now = millis();
    //      Serial.printf(D_STR_TIMESTAMP " : %06u.%03u\n", now / 1000, now % 1000);
    //      // Check if we got an IR message that was to big for our capture buffer.
    //      if (results.overflow)
    //        Serial.printf(D_WARN_BUFFERFULL "\n", kCaptureBufferSize);
    //      // Display the library version the message was captured with.
    //      Serial.println(D_STR_LIBRARY "   : v" _IRREMOTEESP8266_VERSION_ "\n");
    //      // Display the tolerance percentage if it has been change from the default.
    //      if (kTolerancePercentage != kTolerance)
    //        Serial.printf(D_STR_TOLERANCE " : %d%%\n", kTolerancePercentage);
    //      // Display the basic output of what we found.
    //      Serial.print(resultToHumanReadableBasic(&results));
    //      // Display any extra A/C info if we have it.
    //      String description = IRAcUtils::resultAcToString(&results);
    //      if (description.length()) Serial.println(D_STR_MESGDESC ": " + description);
    //      yield();  // Feed the WDT as the text output can take a while to print.
    //  #if LEGACY_TIMING_INFO
    //      // Output legacy RAW timing info of the result.
    //      Serial.println(resultToTimingInfo(&results));
    //      yield();  // Feed the WDT (again)
    //  #endif  // LEGACY_TIMING_INFO
    //      // Output the results as source code
    //      Serial.println(resultToSourceCode(&results));
    //      Serial.println();    // Blank line between entries
    //      yield();             // Feed the WDT (again)

    String lastIrReceived = String(results.decode_type) + kCommandDelimiter[0] +
                            resultToHexidecimal(&results);
    if (results.decode_type == UNKNOWN) {
      lastIrReceived += ";";
      for (uint16_t i = 1; i < results.rawlen; i++) {
        uint32_t usecs;
        for (usecs = results.rawbuf[i] * kRawTick; usecs > UINT16_MAX;
             usecs -= UINT16_MAX) {
          lastIrReceived += uint64ToString(UINT16_MAX);
          lastIrReceived += ",0,";
        }
        lastIrReceived += uint64ToString(usecs, 10);
        if (i < results.rawlen - 1)
          lastIrReceived += ",";
      }
    }
    // If it isn't an AC code, add the bits.
    if (!hasACState(results.decode_type))
      lastIrReceived += kCommandDelimiter[0] + String(results.bits);


    sendmqtt("/receive", lastIrReceived);
    //mqttClient.publish(path.c_str(), lastIrReceived.c_str());
    Serial.print("Incoming IR message sent to MQTT:");
    Serial.println(lastIrReceived.c_str());

    irrecv.resume();  // Receive the next value
  }

}
