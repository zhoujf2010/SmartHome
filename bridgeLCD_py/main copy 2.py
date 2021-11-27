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
from hassclient import HomeAssistantClient
import asyncio

#TODO 分出设备类 读取天气预报 微信对接

class Devices():
    def __init__(self) -> None:
        pass

url = "http://192.168.3.168:8123"
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJlMzJkYmVjMTI4MTk0ZDAxODk1MDY2YTA0MWQ1NDNjNCIsImlhdCI6MTYzMDExODgyNCwiZXhwIjoxOTQ1NDc4ODI0fQ.aBRaWzvHyKixnX1MiCu3uqZ4W2De44n6TynsSjUY1DY"
rooturlpath = "lovelace-wx"


class SocketServer():
    def __init__(self, host_port,HOST = '127.0.0.1'):
        self.port = host_port
        self.host = HOST
        self.clientList =[]

    async def start(self):
        hassclient = HomeAssistantClient(url, token)
        hassclient.register_event_callback(self.receiveHassMsg)
        await hassclient.connect()
        self.hassclient = hassclient

        
        # time.sleep(2)
        # print("ready...1")
        
        # dt = {"type": "call_service", "domain": "switch", "service": "turn_on", "service_data": {"entity_id": "switch.mysmart_d5fa66"}}
        # await hassclient.send_command(dt)

        # time.sleep(2)
        # print("ready...2")
        # dt = {"type": "call_service", "domain": "switch", "service": "turn_off", "service_data": {"entity_id": "switch.mysmart_d5fa66"}}
        # await hassclient.send_command(dt)
        
        loop = asyncio.get_event_loop()
        loop.create_task(self.startServerThd())
        # x = threading.Thread(target=loop.run_in_executor, args=(self.startServerThd(),))
        # # x = threading.Thread(target=self.startServerThd)
        # logger.info("Main    : before running thread")
        # x.start()


    async def startServerThd(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            loop = asyncio.get_event_loop()
            s.listen()
            while True:
                conn, addr = s.accept()
                
                # x = threading.Thread(target=self.between_callback,args=(conn,addr))
                # logger.info("Main    : before running thread")
                # x.start()
                loop.create_task(self.startClient(conn,addr))
                # _thread = threading.Thread(target=asyncio.run, args=(self.startClient(conn,addr),))
                # _thread.start()

    def between_callback(self,conn,addr):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.startClient(conn,addr))
        loop.close()

    async def startClient(self,conn,addr):
        self.clientList.append(conn)
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(10240)
                if not data:
                    break
                # conn.sendall(data)
                await self.hassclient.send_command(json.loads(data.decode("utf-8")))

        self.clientList.remove(conn)

    def receiveHassMsg(self,type,data):
        # print(type,data)
        dt = {'type':type,'data':data}
        sdt = json.dumps(dt)
        # for item in self.clientList:
        #     item.send(sdt.encode("utf-8"))


async def main():
    s = SocketServer(81)
    await s.start()
    logger.info("started")

    _stopped = asyncio.Event()
    await _stopped.wait()




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


    asyncio.run(main())
    logger.info("started")
