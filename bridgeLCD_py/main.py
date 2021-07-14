import websocket
import json
import time
import base64
import sys
import os
import psutil   
import socket

import threading



class SockClient(threading.Thread):

    def __init__(self,msgcallback, host_ip, host_port):
        threading.Thread.__init__(self)
        self.running = False
        self.msgcallback = msgcallback
        self.sock = socket.socket()
        self.sock.settimeout(20)  # 20 seconds
        try:
            self.sock.connect((host_ip, host_port))
            self.sock.settimeout(None)
        except socket.error as e:
            print("Socket Connect Error:%s" % e)
            exit(1)
        self.running = True

        self.error_cnt = 0

    def run(self):
        while self.running:
            try:
                data = self.sock.recv(255)
                if len(data) > 0:              
                    s = data.decode("utf-8") 
                    print(s)    
                    if s == "Hello":
                        self.sendcmd("Hi")  
            except socket.error as e:
                print('socket running error:', str(e))
                break

        print('SockClient Thread Exit\n')

    
    def sendcmd(self, cmd):
        self.sock.send(cmd.encode())

    def sendmethod(self,method, param):
        dt = json.loads(param)
        data = int(dt["msg"])
        # print(data)
        my_bytes = bytearray()
        my_bytes.append(data)

        self.sock.send(my_bytes)

if __name__ == '__main__':
    s = SockClient(None,"192.168.3.215",8266)
    s.sendcmd("aa")
    print(1)
    time.sleep(1)
    s.sendcmd("hello there")
    s.start()
    time.sleep(1000)