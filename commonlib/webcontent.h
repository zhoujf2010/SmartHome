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



String pagecontent1 = "<body>"
                                  "    <h1>mySnoff setup</h1><b>- version: 0.5 -</b>"
                                  "    <table style=\"width:100%;border: 1px solid #fff;\">"
                                  "        <tbody>"
                                  "            <tr>"
                                  "                <th  style=\"text-align:center;width:100%;\">"
                                  "                    <form action=\"/APsubmit\" method=\"POST\">"
                                  "                        <div class=\"row\">"
                                  "                            <div class=\"title\">ID:</div>"
                                  "                            <div class=\"content\"><input type=\"text\" name=\"id\" value=\"\" /></div>"
                                  "                        </div>"
                                  "                        <div class=\"row\">"
                                  "                            <div class=\"title\">SSID:</div>"
                                  "                            <div class=\"content\"><input type=\"text\" name=\"newssid\" value=\"\" /></div>"
                                  "                        </div>"
                                  "                        <div class=\"row\">"
                                  "                            <div class=\"title\">newpass:</div>"
                                  "                            <div class=\"content\"><input type=\"text\" name=\"newpass\" value=\"\" maxlength=\"64\" /></div>"
                                  "                        </div>"
                                  "                        <div class=\"row\">"
                                  "                            <div class=\"title\">mqttIP:</div>"
                                  "                            <div class=\"content\"><input type=\"text\" name=\"mqttIP\" value=\"\" maxlength=\"64\" /></div>"
                                  "                        </div>"
                                  "                        <input type=\"submit\" value=\"提交\" />"
                                  "                    </form>"
                                  "                </th>"
                                  "                <th style=\"text-align:left;width:50%;\"></th>"
                                  "            </tr>"
                                  "        </tbody>"
                                  "    </table>"
                                  "    <br>";
                                  

String pagecontent2 = "    <form action=\"/esprestart\" target=\"_top\"><input type=\"submit\" value=\"重启\"></form>"
                                  "    <form action=\"/cleareeprom\" target=\"_top\"><input type=\"submit\" value=\"清除room\"></form>";

String pagecontent3 = 
                                  "</body>"
                                  "</html>";
