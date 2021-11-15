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


class SocketServer():
    def __init__(self, host_port,HOST = '127.0.0.1'):
        self.port = host_port
        self.host = HOST

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            while True:
                conn, addr = s.accept()
                
                x = threading.Thread(target=self.startClient,args=(conn,addr))
                logger.info("Main    : before running thread")
                x.start()
    
    def startClient(self,conn,addr):
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                conn.sendall(data)



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
    s = SocketServer(81)
    s.start()


    time.sleep(10000)
