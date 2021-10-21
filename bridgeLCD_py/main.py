import websocket
import json
import time
import base64
import sys
import os
import psutil
import socket
import paho.mqtt.client as mqtt
import threading
import datetime
import logging

#TODO 分出设备类 读取天气预报 微信对接

class Devices():
    def __init__(self) -> None:
        pass




class SockClient():

    def __init__(self, msgcallback, host_ip, host_port):
        # threading.Thread.__init__(self)
        self.running = False
        self.msgcallback = msgcallback
        self.host_ip = host_ip
        self.host_port = host_port

        
        self.running = True
        self.connected = False

        self.error_cnt = 0
        self.page0_sel = 0

    def start(self):
        x = threading.Thread(target=self.DoReceive)
        logger.info("Main    : before running thread")
        x.start()
        y = threading.Thread(target=self.SendTime)
        logger.info("Main    : before running thread")
        y.start()

    def SendTime(self):
        olddt = datetime.datetime.now()
        while self.running:
            newdt = datetime.datetime.now()
            dt = newdt - olddt
            if dt.total_seconds() < 5:
                time.sleep(0.5)
                continue
            olddt = newdt
            obj = {}
            obj["type"] = "screensaver"
            obj["data"] = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%w")
            logger.debug("send date")
            self.sendcmd(json.dumps(obj))

    def DoReceive(self):
        while self.running:
            if not self.connected:
                try:
                    self.sock = socket.socket()
                    self.sock.settimeout(5)  # 20 seconds
                    self.sock.connect((self.host_ip, self.host_port))
                    self.sock.settimeout(None)
                    self.connected = True
                    logger.info("socket connected")
                except socket.error as e:
                    logger.error('socket Connect error:' + str(e))
                    pass

            try:
                data = self.sock.recv(255)
                if len(data) > 0:
                    s = data.decode("utf-8")
                    back = self.cmdexchange(s)
                    if back != "":
                        self.sendcmd(back)
            except socket.error as e:
                logger.error('socket running error:' + str(e))
                self.connected = False

        logger.info('SockClient Thread Exit\n')

    def sendcmd(self, cmd):
        try:
            if self.connected:
                self.sock.send(cmd.encode())
        except socket.error as e:
            logger.error('socket send error:' + str(e))
            self.connected = False

    def sendmethod(self, method, param):
        dt = json.loads(param)
        data = int(dt["msg"])
        # print(data)
        my_bytes = bytearray()
        my_bytes.append(data)

        self.sock.send(my_bytes)

    def cmdexchange(self, msg):
        dt = json.loads(msg.strip("\0"))
        logger.info("receive from LCD:" + msg.strip("\0"))
        tp = dt["type"]
        if tp == "init":
            if dt["value"] =="page0":
                obj = {}
                obj["type"] = "page0_init"
                obj["data"] = ["测试灯", "主灯", "筒灯","饭厅灯","电视灯"]#, "房间2","走廊灯","阳台灯"]
                obj["listSel"] = self.page0_sel
                return json.dumps(obj)
        elif tp == "page0":
            if dt["index"] == 0:
                if dt["value"] == 1:
                    self.sendMqtt("homeassistant/switch/MySmart-d5fa66/set","ON")
                elif dt["value"] == 0:
                    self.sendMqtt("homeassistant/switch/MySmart-d5fa66/set","OFF")

        return ""

    def connectMqtt(self, url):
        self.client = mqtt.Client("test")
        self.client.on_connect = self.onMqttConnect
        self.client.on_message = self.onMqttmsg
        self.client.connect("192.168.3.168")

    def sendMqtt(self, url, msg):
        self.client.publish(url, msg)

    def onMqttmsg(self, client, userdata, msg):
        switch = str(msg.payload.decode("utf-8"))
        logger.info('receive from mqtt=>' + msg.topic+" " + switch)

        if msg.topic =="homeassistant/switch/MySmart-d5fa66/state":
            obj = {}
            obj["type"] = "page0"
            obj["index"] = 0
            if switch == "ON":
                obj["value"] = 1
                self.page0_sel = self.page0_sel | 0x01
            elif switch == "OFF":
                obj["value"] = 0
                self.page0_sel = self.page0_sel & ~0x01

            self.sendcmd(json.dumps(obj))

    def onMqttConnect(self, client, userdata, flags, rc):
        logger.info("MQTT Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.v
        client.subscribe(self.url)
        # client.subscribe(self.url + "/stat")
        # client.subscribe(self.url + "/stat")
        # client.subscribe(self.url + "/ip")
        # client.subscribe(self.url + "/Temperature")
        # client.subscribe(self.url + "/Humidity")



if __name__ == '__main__':
    # create logger with 'spam_application'
    logger = logging.getLogger('bridgeLCD')
    logger.setLevel(logging.INFO)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('log.log')
    fh.setLevel(logging.INFO)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)


    logger.info("started")
    s = SockClient(None, "192.168.3.182", 81)
    # s = SockClient(None, "100.85.157.158", 81)
    s.start()

    # url = 'home/mylightsensor/MySonoff-df62df' #太阳能
    # url = 'home/myhcsr/MySonoff-e37fff' #人体感应
    # url = 'home/mydht11/MySonoff-e7236f' #温度
    url = "home/sonoff/MySonoff-d5fa66"  # LED
    s.url = "#"

    s.connectMqtt("")
    # client =mqtt.Client("test")
    # client.on_connect = s.onMqttConnect
    # client.on_message = s.onMqttmsg
    # client.connect("192.168.3.168")
    # client.publish(url,"stat")

    
    s.client.loop_forever()

    s.client.disconnect()

    time.sleep(1000)
