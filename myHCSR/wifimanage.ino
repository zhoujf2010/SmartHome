
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <EEPROM.h>
#include "wifimanage.h"
#include "webcontent.h"

ESP8266WebServer server(80);

//加载页面
void handle_AProot() {
  String SServerSend;
  SServerSend = pageheader;

  String script = "<script>";
  script += "document.getElementsByName(\"id\")[0].value=\"" + readID() + "\";";
  script += "document.getElementsByName(\"newssid\")[0].value=\"" + readesid() + "\";";
  script += "document.getElementsByName(\"mqttIP\")[0].value=\"" + readmqttip() + "\";";
  script += "</script>";

  SServerSend += pagecontent1 + pagecontent2 + script + pagecontent3;
  server.send(200, "text/html", SServerSend);
  delay(100);
}

//清除room内容
void handle_clearAPeeprom() {
  Serial.println(F("! Clearing eeprom ! "));
  clearroom();
  Serial.println(F("! Finished ! Restarting in 1 sec! !"));
  delay(1000);
  ESP.restart();
}

//重启
void handle_APrestart() {
  Serial.println(F("! Restarting in 1 sec! !"));
  delay(1000);
  ESP.restart();
}


//提交数据，写入room
void handle_APsubmit() {
  String thenewssid = server.arg("newssid");
  String thenewpass = server.arg("newpass");
  String theid = server.arg("id");
  String themqttIP = server.arg("mqttIP");

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

    String APwebstring = "";   // String to display
    if (EEPROM.commit())
      APwebstring = F("<div class=\"info\">Saved to eeprom... restart to boot into new wifi</div><br>\n");
    else
      APwebstring = F("<div class=\"info\">Couldn't write to eeprom. Please try again.</div><br>\n");

    String SServerSend;
    SServerSend = pageheader;
    SServerSend += pagecontent1 + APwebstring + pagecontent2 + pagecontent3;
    server.send(200, "text/html", SServerSend);
  }
}



// get available AP to connect + HTML list to display
void getAPlist() {
  WiFi.disconnect();
  delay(100);
  int n = WiFi.scanNetworks();
  Serial.println(F("Scan done"));
  String APwebstring ="";
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


void clearroom() {
  for (int i = 0; i < 225; ++i) {
    EEPROM.write(i, 0);
  }
  EEPROM.commit();
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
    id = "MySonoff-" + macID;
  }
  return id;
}

String readmqttip() {
  return readData(160, 64);
}


String readesid() {
  return readData(0, 32);
}


//0-32 SID
//33-96 password
//160-224 mqttip
//225 resettimes

void startWifi() {
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
    currentIP = WiFi.localIP().toString();
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
    currentIP = WiFi.softAPIP().toString();
  }

  server.on("/", handle_AProot);
  server.on("/APsubmit", handle_APsubmit);
  server.on("/esprestart", handle_APrestart);
  server.on("/cleareeprom", handle_clearAPeeprom);
  server.begin();
  Serial.println("HTTP server started");
}

void wifiloop() {


  
  server.handleClient();                    // Listen for HTTP requests from clients
}
