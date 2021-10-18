#include <Ticker.h>
#include "src/commonlib/wifimanage.h"
#include "src/commonlib/otatool.h"
#include "src/commonlib/common.h"
#include <EEPROM.h>



//易微联设备
String firmversion =    "2.2";
String DEVICE      =    "switch";
#define BUTTON          0
#define BUTTON1         9
#define BUTTON2         10
#define RELAY           12
#define RELAY1          5
#define RELAY2          4
#define LED             13
#define LEDON           LOW
#define LEDOFF          HIGH


Ticker btn_timer;
Ticker led_timer;

unsigned long count = 0;                                     // (Do not Change)
unsigned long count1 = 0;                                     // (Do not Change)
unsigned long count2 = 0;                                     // (Do not Change)
bool sendStatus = false;                                     // (Do not Change)
bool sendStatus1 = false;                                     // (Do not Change)
bool sendStatus2 = false;                                     // (Do not Change)
bool requestRestart = false;                                 // (Do not Change)
int switchNum = 0; //几路开关

String MQTT_TOPIC = "";
ESP8266WebServer* inner_server;

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

  //设置IO口模式
  pinMode(BUTTON, INPUT);
  pinMode(BUTTON1, INPUT);
  pinMode(BUTTON2, INPUT);

  pinMode(LED, OUTPUT);
  pinMode(RELAY, OUTPUT);
  pinMode(RELAY1, OUTPUT);
  pinMode(RELAY2, OUTPUT);
  digitalWrite(LED, LEDOFF);

  delay(10);
  Serial.println("ready set");

  switchNum = readCusVal(3);
  Serial.println("switchNum:" + String(switchNum));

  //恢复上次开关状态
  digitalWrite(RELAY, readCusVal(0) == 1 ? HIGH : LOW);
  digitalWrite(RELAY1, readCusVal(1) == 1 ? HIGH : LOW);
  digitalWrite(RELAY2, readCusVal(2) == 1 ? HIGH : LOW);
  Serial.println("finish set");
  delay(2000); //需要延时2秒，三路的不然会影响按健
  Serial.println("go");
  btn_timer.attach(0.05, button);
  led_timer.attach(0.5, blink);

  inner_server = startWifi();  //连接网络信息
  inner_server->on("/cfg", handle_cfg);
  inner_server->on("/APsubmit2", handle_APsubmit2);

  initOTA(LED);// 初使化OTA模式

  led_timer.detach();
  led_timer.attach(0.2, blink);

  String MQTT_TOPIC = "homeassistant/" + DEVICE + "/" + readID();
  initMQTT(MQTT_TOPIC, "/set", false, callback);

  String cfg = String("{");
  cfg += "\"name\": \"" + readID() + "\"";
  cfg += ",\"unique_id\":\"" + readID() + "\"";
  cfg += ",\"command_topic\": \"homeassistant/" + DEVICE + "/" + readID() + "/set\"";
  cfg += ",\"state_topic\": \"homeassistant/" + DEVICE + "/" + readID() + "/state\"";
  cfg += "}";

  Serial.println(cfg);
  sendmqtt("/config", cfg);

  if (switchNum == 3) {
    cfg = String("{");
    cfg += "\"name\": \"" + readID() + "_2\"";
    cfg += ",\"unique_id\":\"" + readID() + "_2\"";
    cfg += ",\"command_topic\": \"homeassistant/" + DEVICE + "/" + readID() + "/set\"";
    cfg += ",\"state_topic\": \"homeassistant/" + DEVICE + "/" + readID() + "/state\"";
    cfg += ",\"payload_on\":\"ON2\",\"state_on\":\"ON2\"";
    cfg += ",\"payload_off\":\"OFF2\",\"state_off\":\"OFF2\"";
    cfg += "}";
    Serial.println(cfg);
    sendmqtt("homeassistant/" + DEVICE + "/" + readID() + "_2/config", cfg);

    cfg = String("{");
    cfg += "\"name\": \"" + readID() + "_3\"";
    cfg += ",\"unique_id\":\"" + readID() + "_3\"";
    cfg += ",\"command_topic\": \"homeassistant/" + DEVICE + "/" + readID() + "/set\"";
    cfg += ",\"state_topic\": \"homeassistant/" + DEVICE + "/" + readID() + "/state\"";
    cfg += ",\"payload_on\":\"ON3\",\"state_on\":\"ON3\"";
    cfg += ",\"payload_off\":\"OFF3\",\"state_off\":\"OFF3\"";
    cfg += "}";
    Serial.println(cfg);
    sendmqtt("homeassistant/" + DEVICE + "/" + readID() + "_3/config", cfg);
  }

  StartFinish();

  led_timer.detach();
  digitalWrite(LED, LEDON); //灯常亮，表示连接成功
}



//加载页面
void handle_cfg() {

  String pageheader = "<!DOCTYPE html>"
                      "<html>"
                      "<head>"
                      "    <meta charset=\"utf-8\">"
                      "    <meta name=\"viewport\" content=\"width=device-width initial-scale=1maximum-scale=1 user-scalable=no\">"
                      "    <meta name=\"apple-mobile-web-app-capable\" content=\"yes\">"
                      "    <meta name=\"apple-mobile-web-app-status-bar-style\" content=\"black\">"
                      "    <meta http-equiv=\"Content-Type\" content=\"text/html; charset=UTF-8\">"
                      "    <title>esp8266 WiFi setup control</title>"
                      "    <style type=\"text/css\">"
                      "        body {"
                      "            text-align: center;"
                      "            font-family: sans-serif;"
                      "            background-color: #000;"
                      "            color: #fff;"
                      "            font-size: 1.2em;"
                      "        }"
                      "        .row{"
                      "            height:30px;"
                      "        }"
                      "        .title{"
                      "            float: left;"
                      "            width:120px;"
                      "        }"
                      "        .content{"
                      "            float: left;"
                      "        }"
                      "        .info{"
                      "            color:red"
                      "        }"
                      "    </style>"
                      "</head>";


  String SServerSend;
  SServerSend = pageheader;

  String pagecontent1 = "<body>"
                        "    <h1>额外配置</h1>"
                        "    <table style=\"width:100%;border: 1px solid #fff;\">"
                        "        <tbody>"
                        "            <tr>"
                        "                <th  style=\"text-align:center;width:100%;\">"
                        "                    <form action=\"/APsubmit2\" method=\"POST\">"
                        "                        <div class=\"row\">"
                        "                            <div class=\"title\">几路开关:</div>"
                        "                            <div class=\"content\"><input type=\"text\" name=\"num\" value=\"\" /></div>"
                        "                        </div>"
                        "                        <input type=\"submit\" value=\"提交\" />"
                        "                    </form>"
                        "                </th>"
                        "                <th style=\"text-align:left;width:50%;\"></th>"
                        "            </tr>"
                        "        </tbody>"
                        "    </table>"
                        "    <br>";

  String script = "<script>";
  script += "document.getElementsByName(\"num\")[0].value=\"" + String(switchNum) + "\";";
  script += "</script>";

  String pagecontent3 =
    "</body>"
    "</html>";
  SServerSend += pagecontent1 + script + pagecontent3;
  inner_server->send(200, "text/html", SServerSend);
  delay(1);
}

void handle_APsubmit2() {
  String num = inner_server->arg("num");
  Serial.println("num:" + num);
  writeCusVal(3, num.toInt());
  inner_server->send(200, "text/html", "<form action=\"/esprestart\" target=\"_top\"><input type=\"submit\" value=\"restart\"></form>");
}

void blink() {
  digitalWrite(LED, !digitalRead(LED));
}

unsigned long lastPress;
int presstimes = 0;
//按钮处理
void button() {
  if (!digitalRead(BUTTON)) {
    count++;
    if (count > 100) {//长按5秒
      digitalWrite(LED, LEDON); //亮起
    }
  }
  else {
    if (count > 1 && count <= 40) {
      digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
      digitalWrite(RELAY, !digitalRead(RELAY));
      sendStatus = true;
      sendmqtt("/log", "press button");

      presstimes ++; //记录3秒内连接压
      if ((millis() > lastPress + (3000)) || (millis() < lastPress)) {
        lastPress = millis();
        presstimes = 0;
      }
      if (presstimes >= 5) {
        Serial.println("\n\nSonoff Rebooting . . . . . . . . Please Wait");
        clearroom();
        blinkLED(LED, 400, 4);
        ESP.restart();
      }
    }
    count = 0;
  }

  if (!digitalRead(BUTTON1)) {
    count1++;
  }
  else {
    if (count1 > 1 && count1 <= 40) {
      digitalWrite(RELAY1, !digitalRead(RELAY1));
      sendStatus1 = true;
    }
    count1 = 0;
  }

  if (!digitalRead(BUTTON2)) {
    count2++;
  }
  else {
    if (count2 > 1 && count2 <= 40) {
      digitalWrite(RELAY2, !digitalRead(RELAY2));
      sendStatus2 = true;
    }
    count2 = 0;
  }
}

unsigned long checkLastTime;

void callback(String topic, String payload_string) {
  Serial.println("receive topic:" + topic);
  Serial.println("receive payload:" + payload_string);
  String payload = payload_string;
  sendmqtt("/log", "receive mqtt: " + payload);

  if (payload == "stat") {
  }
  else if (payload == "ON") {
    digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
    digitalWrite(RELAY, HIGH);
    writeCusVal(0, 1);
    sendStatus = true;
  }
  else if (payload == "OFF") {
    digitalWrite(LED, LEDOFF); //有操作后，状态灯就关闭
    digitalWrite(RELAY, LOW);
    writeCusVal(0, 0);
    sendStatus = true;
  }
  else if (payload == "ON2") {
    digitalWrite(RELAY1, HIGH);
    writeCusVal(1, 1);
    sendStatus1 = true;
  }
  else if (payload == "OFF2") {
    digitalWrite(RELAY1, LOW);
    writeCusVal(1, 0);
    sendStatus1 = true;
  }
  else if (payload == "ON3") {
    digitalWrite(RELAY2, HIGH);
    writeCusVal(2, 1);
    sendStatus2 = true;
  }
  else if (payload == "OFF3") {
    digitalWrite(RELAY2, LOW);
    writeCusVal(2, 0);
    sendStatus2 = true;
  }
  else if (payload == "reset") {
    blinkLED(LED, 400, 4);
    ESP.restart();
  }
}


void loop() {
  if (loopOTA())
    return ;
  wifiloop();

  if (sendStatus) { //发送至mq
    if (digitalRead(RELAY) == HIGH)  {
      sendmqtt("/state", "ON");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . ON");
      writeCusVal(0, 1);

    } else {
      sendmqtt("/state", "OFF");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . OFF");
      writeCusVal(0, 0);
    }
    sendStatus = false;
  }
  if (sendStatus1) { //发送至mq
    if (digitalRead(RELAY1) == HIGH)  {
      sendmqtt("/state", "ON2");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . ON2");
      writeCusVal(1, 1);
    } else {
      sendmqtt("/state", "OFF2");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . OFF2");
      writeCusVal(1, 0);
    }
    sendStatus1 = false;
  }
  if (sendStatus2) { //发送至mq
    if (digitalRead(RELAY2) == HIGH)  {
      sendmqtt("/state", "ON3");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . ON3");
      writeCusVal(2, 1);
    } else {
      sendmqtt("/state", "OFF3");
      Serial.println("Relay . . . . . . . . . . . . . . . . . . OFF3");
      writeCusVal(2, 0);
    }
    sendStatus2 = false;
  }
}
