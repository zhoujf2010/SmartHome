
#include <ESP8266WiFi.h>
#include <EEPROM.h>
#include "wifimanage.h"
#include "common.h"
#include <PubSubClient.h>
#include "webcontent.h"

String CurrentVersion = "1.0";
String devicetype = "";
int connectType = 0;

ESP8266WebServer server(80);
String readesid();
String printEncryptionType(int thisType);

void setVersion(String version) {
  CurrentVersion = version;
}

void setdevicetype(String type) {
  devicetype = type;
}

//加载页面
void handle_AProot() {
  String SServerSend;
  SServerSend = pageheader;

  String script = "<script>";
  script += "document.getElementsByName(\"id\")[0].value=\"" + readID() + "\";";
  script += "document.getElementsByName(\"newssid\")[0].value=\"" + readesid() + "\";";
  script += "document.getElementsByName(\"mqttIP\")[0].value=\"" + readmqttip() + "\";";
  script += "</script>";

  pagecontent1.replace("%CurrentVersion%", CurrentVersion);
  SServerSend += pagecontent1 + pagecontent2 + script + pagecontent3;
  server.send(200, "text/html", SServerSend);
  delay(1);
}


void handle_version() {
  server.send(200, "text/html", CurrentVersion);
  delay(1);
}


void handle_name() {
  server.send(200, "text/html", readID());
  delay(1);
}

void handle_devicetype() {
  server.send(200, "text/html", devicetype);
  delay(1);
}

bool NeedRestart = false;

//清除room内容
void handle_clearAPeeprom() {
  Serial.println(F("! Clearing eeprom ! "));
  clearroom();
  server.send(200, "text/html", "OK");
  NeedRestart = true;
}

//重启
void handle_APrestart() {
  server.send(200, "text/html", "OK");
  NeedRestart = true;
}


//提交数据，写入room
void handle_APsubmit() {
  String thenewssid = server.arg("newssid");
  String thenewpass = server.arg("newpass");
  String theid = server.arg("id");
  String themqttIP = server.arg("mqttIP");

  String APwebstring = "";   // String to display
  if (thenewssid != "") {
    Serial.println(F("! Clearing eeprom !"));
    clearroom();

    Serial.println(F("Writing SSID to EEPROM"));
    for (int i = 0; i < thenewssid.length(); ++i)
      EEPROM.write(i, thenewssid[i]);

    Serial.println(F("Writing password to EEPROM"));
    for (int i = 0; i < thenewpass.length(); ++i)
      EEPROM.write(32 + i, thenewpass[i]);

    Serial.println(F("Writing id to EEPROM"));
    for (int i = 0; i < theid.length(); ++i)
      EEPROM.write(96 + i, theid[i]);

    Serial.println(F("Writing themqttIP to EEPROM"));
    for (int i = 0; i < themqttIP.length(); ++i)
      EEPROM.write(160 + i, themqttIP[i]);

    if (EEPROM.commit())
      APwebstring = F("<div class=\"info\">Saved to eeprom... restart to boot into new wifi</div><br>\n");
    else
      APwebstring = F("<div class=\"info\">Couldn't write to eeprom. Please try again.</div><br>\n");

  }
  String SServerSend;
  SServerSend = pageheader;
  SServerSend += pagecontent1 + APwebstring + pagecontent2 + pagecontent3;
  server.send(200, "text/html", SServerSend);
}



// get available AP to connect + HTML list to display
void getAPlist() {
  WiFi.disconnect();
  delay(100);
  int n = WiFi.scanNetworks();
  Serial.println(F("Scan done"));
  String APwebstring = "";
  if (n == 0) {
    Serial.println(F("No networks found :("));
    APwebstring = F("No networks found :(");
    return;
  }

  // sort by RSSI
  int indices[n];
  for (int i = 0; i < n; i++) {
    indices[i] = i;
  }
  for (int i = 0; i < n; i++) {
    for (int j = i + 1; j < n; j++) {
      if (WiFi.RSSI(indices[j]) > WiFi.RSSI(indices[i])) {
        std::swap(indices[i], indices[j]);
      }
    }
  }

  Serial.println("");
  // HTML Print SSID and RSSI for each network found
  APwebstring = F("<ul>");
  for (int i = 0; i < n; ++i)
  {
    APwebstring += F("<li>");
    APwebstring += i + 1;
    APwebstring += F(":&nbsp;&nbsp;<b>");
    APwebstring += F("<a href=\"#\" target=\"_top\" onClick=\"document.getElementById(\'formnewssid\').value=\'");
    APwebstring += WiFi.SSID(indices[i]);
    APwebstring += F("\'\">");
    APwebstring += WiFi.SSID(indices[i]);
    APwebstring += F("</a>");
    APwebstring += F("</b>&nbsp;&nbsp;&nbsp;(");
    APwebstring += WiFi.RSSI(indices[i]);
    APwebstring += F("&nbsp;dBm)&nbsp;&nbsp;&nbsp;");
    APwebstring += printEncryptionType(WiFi.encryptionType(indices[i]));
    APwebstring += F("</li>");
  }
  APwebstring += F("</ul>");
  delay(100);
  Serial.println("");
  for (int i = 0; i < n; ++i)
  {
    Serial.print((i + 1));
    Serial.println(". " + WiFi.SSID(indices[i]) + " " + WiFi.RSSI(indices[i]) + " " + printEncryptionType(WiFi.encryptionType(indices[i])));
  }
  Serial.println("");
  delay(100);
}


// return the connection type for the AP list
String printConnectionType(int thisType) {
  String con_type = "";
  // read connection type and print out the name:
  switch (thisType) {
    case 255:
      return con_type = "WL_NO_SHIELD";
    case 0:
      return con_type = "WL_IDLE_STATUS";
    case 1:
      return con_type = "WL_NO_SSID_AVAIL";
    case 2:
      return con_type = "WL_SCAN_COMPLETED";
    case 3:
      return con_type = "WL_CONNECTED";
    case 4:
      return con_type = "WL_CONNECT_FAILED";
    case 5:
      return con_type = "WL_CONNECTION_LOST";
    case 6:
      return con_type = "WL_DISCONNECTED";
    default:
      return con_type = "?";
  }
}

// return the connection type for the AP list
String printEncryptionType(int thisType) {
  String enc_type = "";
  // read the encryption type and print out the name:
  switch (thisType) {
    case ENC_TYPE_WEP:
      return enc_type = "WEP";
    case ENC_TYPE_TKIP:
      return enc_type = "WPA";
    case ENC_TYPE_CCMP:
      return enc_type = "WPA2";
    case ENC_TYPE_NONE:
      return enc_type = "None";
    case ENC_TYPE_AUTO:
      return enc_type = "Auto";
    default:
      return enc_type = "?";
  }
}




String readData(int startPos, int len) {
  String data = "";
  for (int i = startPos; i < startPos + len; ++i)
  {
    int ch = EEPROM.read(i);
    if (ch == 0)
      break;
    data += char(ch);
  }
  return data;
}


String readID() {
  String id = readData(96, 64);

  if (id == "") {
    id = String(ESP.getChipId());
    uint8_t mac[WL_MAC_ADDR_LENGTH];
    WiFi.softAPmacAddress(mac);
    String macID = String(mac[WL_MAC_ADDR_LENGTH - 3], HEX) +
                   String(mac[WL_MAC_ADDR_LENGTH - 2], HEX) +
                   String(mac[WL_MAC_ADDR_LENGTH - 1], HEX);
    macID.toLowerCase();
    id = "MySmart-" + macID;
  }
  return id;
}

String readmqttip() {
  return readData(160, 64);
}


String readesid() {
  return readData(0, 32);
}

String getIP() {
  if (connectType == 1) { //连接wifi
    return WiFi.localIP().toString();
  }
  else if (connectType == 2) { //启动热点
    return WiFi.softAPIP().toString();
  }
  return "";
}

//0-32 SID
//33-96 password
//160-224 mqttip
//225 resettimes

ESP8266WebServer* startWifi() {
  String esid = readesid();
  String epass = readData(32, 64);
  String id = readID();
  String mqttip = readmqttip();

  Serial.print("SSID: ");
  Serial.println(esid);
  Serial.print("PASS: ");
  Serial.println(epass);
  Serial.print("id: ");
  Serial.println(id);
  Serial.print("mqttip: ");
  Serial.println(mqttip);

  if (esid != "") { //连接wifi
    Serial.println();
    Serial.print("Connecting to ");
    Serial.println(esid);

    WiFi.mode(WIFI_STA);
    WiFi.hostname(id);
    WiFi.begin(esid, epass);//启动

    //在这里检测是否成功连接到目标网络，未连接则阻塞。
    while (WiFi.status() != WL_CONNECTED)
    {
      delay(500);
      Serial.print(".");
    }
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    connectType = 1;
  }
  else { //启动热点

    WiFi.mode(WIFI_AP);

    char AP_NameChar[id.length() + 1];
    char AP_password[] = "12345678";
    memset(AP_NameChar, 0, id.length() + 1);
    for (int i = 0; i < id.length(); i++)
      AP_NameChar[i] = id.charAt(i);

    getAPlist();
    WiFi.softAP(AP_NameChar, AP_password);
    Serial.print(F("started AP, name: "));
    Serial.println(id);
    Serial.print(F("SoftAP IP address: "));
    Serial.println(WiFi.softAPIP());
    connectType = 2;
  }

  server.on("/", handle_AProot);
  server.on("/APsubmit", handle_APsubmit);
  server.on("/esprestart", handle_APrestart);
  server.on("/cleareeprom", handle_clearAPeeprom);
  server.on("/version", handle_version);
  server.on("/name", handle_name);
  server.on("/devicetype", handle_devicetype);
  server.begin();
  Serial.println("HTTP server started");
  return &server;
}


WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
bool hasmqtt = false;

String _MQTT_TOPIC = "";
String _subtopic = "";
std::function<void(String topic, String payload)> _callback;
std::function<void()> _initDevice;
bool firstconnect = false;

void innercallback(char* topic, byte* payload, unsigned int length) {
  String topic_str = String(topic);

  String payload_string = "";
  for (int i = 0; i < length; ++i)
    payload_string += char(payload[i]);

  if (firstconnect) { //抛弃首次数据
    firstconnect = false;
    Serial.println("del:" + payload_string);
    return ;
  }
  _callback(topic_str, payload_string);

  if (payload_string == "reinit")
    _initDevice();
}

boolean _ignorefirstmsg = false;

void initMQTT(String MQTT_TOPIC, String subtopic, boolean ignorefirstmsg, std::function<void(String topic, String payload)> callback, std::function<void()> initDevice) {
  _MQTT_TOPIC = MQTT_TOPIC;
  _subtopic = subtopic;
  _callback = callback;
  _initDevice = initDevice;
  _ignorefirstmsg = ignorefirstmsg;
  if (readmqttip() != "") {
    char* c = new char[200];  //深度copy一下，否则直接用就不行
    strcpy(c, readmqttip().c_str());
    mqttClient.setServer(c, 1883);
    mqttClient.setCallback(innercallback);
    hasmqtt = true;
    connectMQTT();
  }
}


void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (mqttClient.connect(readID().c_str())) {
      Serial.println("connected");

      mqttClient.subscribe((_MQTT_TOPIC + _subtopic).c_str());
      mqttClient.setBufferSize(5120);
      Serial.println("Topic:" + _MQTT_TOPIC);
      firstconnect = true;
      if (!_ignorefirstmsg) //可配置首次不跳过
        firstconnect = false;
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);// Wait 5 seconds before retrying
    }
  }
  _initDevice();
}

void sendmqtt(String path, String msg) {
  String path2 = path;
  if (path.startsWith("/"))
    path2 = _MQTT_TOPIC + path;
  if (hasmqtt && mqttClient.connected()) {
    mqttClient.publish(path2.c_str(), msg.c_str());
//    Serial.println("send [" + path2 + "] msg:" + msg);
  }
}


int kUpdFreq = 1;                                            // Update frequency in Mintes to check for mqtt connection
int kRetries = 10;                                           // WiFi retry count. Increase if not connecting to router.
unsigned long TTasks;
void timedTasks() {
  if ((millis() > TTasks + (kUpdFreq * 60000)) || (millis() < TTasks)) {
    TTasks = millis();
    checkConnection();
  }
}


void checkConnection() {
  if (connectType == 1) { //连接wifi
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi.status() != WL_CONNECTED), Restarted wifi");
      //ESP.restart();
      startWifi();
    }
  }
  //  if (WiFi.status() == WL_CONNECTED)  {
  //    if (mqttClient.connected()) {
  //      Serial.println("mqtt broker connection . . . . . . . . . . OK");
  //    }
  //    else {
  //      Serial.println("mqtt broker connection . . . . . . . . . . LOST");
  //      requestRestart = true;
  //    }
  //  }
  //  else {
  //    Serial.println("WiFi connection . . . . . . . . . . LOST");
  //    requestRestart = true;
  //  }

  //  if (!mqttClient.connected()) {
  //    //    if (!isconnecting) {
  //    //      isconnecting = true;
  //    //      Serial.println("start connect mqtt");
  //    //      mqtt_timer.once(0.1, reconnect);
  //    //      mqtt_timer.detach();
  //    //    }
  //
  //    Serial.print("Attempting MQTT connection...");
  //    if (mqttClient.connect(readID().c_str())) {
  //      Serial.println("connected");
  //      mqttClient.subscribe(MQTT_TOPIC);
  //    } else {
  //      Serial.print("failed, rc=");
  //      Serial.print(mqttClient.state());
  //      Serial.println(" try again in 5 seconds");
  //      // Wait 5 seconds before retrying
  ////      delay(5000);
  //    }
  //  }
}



void wifiloop() {
  if (NeedRestart) {
    Serial.println(F("! Restarting in 1 sec! !"));
    delay(1000);
    ESP.restart();
    return;
  }

  timedTasks();


  server.handleClient();                    // Listen for HTTP requests from clients


  if (hasmqtt && !mqttClient.connected()) {
    connectMQTT();
  }

  if (hasmqtt)
    mqttClient.loop();
}
