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

    def start(self):
        x = threading.Thread(target=self.DoReceive)
        logging.info("Main    : before running thread")
        x.start()
        y = threading.Thread(target=self.SendTime)
        logging.info("Main    : before running thread")
        y.start()

    def SendTime(self):
        olddt = datetime.datetime.now()
        while self.running:
            newdt = datetime.datetime.now()
            dt = newdt - olddt
            if dt.total_seconds() <5:
                continue
            olddt = newdt
            obj = {}
            obj["type"] = "screensaver"
            obj["data"] = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%w")
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
                except socket.error as e:
                    print("Socket Connect Error:%s" % e)
                    pass

            try:
                data = self.sock.recv(255)
                if len(data) > 0:
                    s = data.decode("utf-8")
                    back = self.cmdexchange(s)
                    if back != "":
                        self.sendcmd(back)
            except socket.error as e:
                print('socket running error:', str(e))
                self.connected = False

        print('SockClient Thread Exit\n')

    def sendcmd(self, cmd):
        try:
            if self.connected:
                self.sock.send(cmd.encode())
        except socket.error as e:
            print('socket running error:', str(e))
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
        print(dt)
        tp = dt["type"]
        if tp == "init":
            if dt["value"] =="page0":
                obj = {}
                obj["type"] = "page0_init"
                obj["data"] = ["测试灯", "主灯", "筒灯","饭厅灯","电视灯"]#, "房间2","走廊灯","阳台灯"]
                obj["listSel"] = 1
                return json.dumps(obj)
        elif tp == "page0":
            if dt["index"] == 0:
                if dt["value"] == 1:
                    self.sendMqtt("on")
                elif dt["value"] == 0:
                    self.sendMqtt("off")

        return ""

    def connectMqtt(self, url):
        self.client = mqtt.Client("test")
        self.client.on_connect = self.onMqttConnect
        self.client.on_message = self.onMqttmsg
        self.client.connect("192.168.3.168")

    def sendMqtt(self, msg):
        self.client.publish(self.url, msg)

    def onMqttmsg(self, client, userdata, msg):
        switch = str(msg.payload.decode("utf-8"))
        print(msg.topic+" " + switch)
        obj = {}
        obj["type"] = "page0"
        obj["index"] = 0
        if switch == "on":
            obj["value"] = 1
        elif switch == "off":
            obj["value"] = 0

        self.sendcmd(json.dumps(obj))

    def onMqttConnect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(self.url + "/stat")
        client.subscribe(self.url + "/ip")
        client.subscribe(self.url + "/Temperature")
        client.subscribe(self.url + "/Humidity")



if __name__ == '__main__':
    s = SockClient(None, "192.168.3.215", 81)
    s.sendcmd("aa")
    print(1)
    time.sleep(1)
    s.sendcmd("hello thereasdfasd")
    s.start()

    # url = 'home/mylightsensor/MySonoff-df62df' #太阳能
    # url = 'home/myhcsr/MySonoff-e37fff' #人体感应
    # url = 'home/mydht11/MySonoff-e7236f' #温度
    url = "home/sonoff/MySonoff-d5fa66"  # LED
    s.url = url

    s.connectMqtt("")
    # client =mqtt.Client("test")
    # client.on_connect = s.onMqttConnect
    # client.on_message = s.onMqttmsg
    # client.connect("192.168.3.168")
    # client.publish(url,"stat")

    
    s.client.loop_forever()

    s.client.disconnect()

    time.sleep(1000)
