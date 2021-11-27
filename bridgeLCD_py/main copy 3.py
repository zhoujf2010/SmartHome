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


url = "http://192.168.3.168:8123"
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJlMzJkYmVjMTI4MTk0ZDAxODk1MDY2YTA0MWQ1NDNjNCIsImlhdCI6MTYzMDExODgyNCwiZXhwIjoxOTQ1NDc4ODI0fQ.aBRaWzvHyKixnX1MiCu3uqZ4W2De44n6TynsSjUY1DY"
rooturlpath = "lovelace-wx"

# 测试命令
# dt = {"type": "call_service", "domain": "switch", "service": "turn_on", "service_data": {"entity_id": "switch.mysmart_d5fa66"}}
# dt = {"type": "call_service", "domain": "switch", "service": "turn_off", "service_data": {"entity_id": "switch.mysmart_d5fa66"}}


class SocketServer():
    def __init__(self, host_port, HOST='0.0.0.0'):
        self.port = host_port
        self.host = HOST
        self.clientList = []
        self.loop = asyncio.get_event_loop()

    async def start(self):
        self.hassclient = hassclient = HomeAssistantClient(url, token)
        hassclient.register_event_callback(self.receiveHassMsg)
        await hassclient.connect()
        logger.info("连接至hass")

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(8)
        server.setblocking(False)
        logger.info("启动socket监听")

        while True:
            client, addr = await self.loop.sock_accept(server)
            self.loop.create_task(self.startClient(client, addr))

    async def startClient(self, conn, addr):
        self.clientList.append(conn)
        with conn:
            logger.info("客户端连接进入%s" % str(addr))
            try:
                while conn:
                    data = (await self.loop.sock_recv(conn, 10240)).decode('utf8')
                    if data:
                        logger.debug("收到屏指令：%s" % data)
                        await self.hassclient.send_command(json.loads(data))
            except socket.error as e:
                logger.error('socket Receive error:' + str(e))

        self.clientList.remove(conn)

    async def receiveHassMsg(self, type, data):
        #收到hass消息发送至客户端
        dt = json.dumps({'type': type, 'data': data})
        logger.debug("sendto screen[%d]:"%len(self.clientList))
        for client in self.clientList:
            try:
                await self.loop.sock_sendall(client, dt.encode('utf8'))
            except socket.error as e:
            except socket.error as e:
                logger.error('socket Send error:' + str(e))
                client.close()
        logger.debug("sendto OK")


async def main():
    s = SocketServer(8082)
    await s.start()
    logger.info("started")

    _stopped = asyncio.Event()
    await _stopped.wait()


if __name__ == '__main__':
    # create logger with 'spam_application'
    logger = logging.getLogger('bridgeLCD')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('log.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    asyncio.run(main())
    logger.info("started")
