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


_LOGGER = logging.getLogger(__name__)

url = "http://192.168.3.168:8123"
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJlMzJkYmVjMTI4MTk0ZDAxODk1MDY2YTA0MWQ1NDNjNCIsImlhdCI6MTYzMDExODgyNCwiZXhwIjoxOTQ1NDc4ODI0fQ.aBRaWzvHyKixnX1MiCu3uqZ4W2De44n6TynsSjUY1DY"
#rooturlpath = "lovelace-wx"

# url = "http://127.0.0.1:8123"
# token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhMmJiOTM2ZTFlMTY0M2EzOGU5N2IwZTQ3YTAxNDdlZiIsImlhdCI6MTYzNzEyMTU0MywiZXhwIjoxOTUyNDgxNTQzfQ.vcjMup4yoacaVSGVHy3RszvH4yomuc1VVW4YIhl-zAM"

# 测试命令
# dt = {"type": "call_service", "domain": "switch", "service": "turn_on", "service_data": {"entity_id": "switch.mysmart_d5fa66"}}
# dt = {"type": "call_service", "domain": "switch", "service": "turn_off", "service_data": {"entity_id": "switch.mysmart_d5fa66"}}

class SocketServer():
    def __init__(self, host_port, HOST='0.0.0.0'):
        self.port = host_port
        self.host = HOST
        self.clientList = {}
        self.loop = asyncio.get_event_loop()

    async def start(self):
        self.hassclient = hassclient = HomeAssistantClient(url, token)
        # hassclient.register_event_callback(self.receiveHassMsg)
        hassclient.register_Msg_callback(self.receiveHassMsg)

        await hassclient.connect()
        _LOGGER.info("连接至hass")

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(8)
        server.setblocking(False)
        _LOGGER.info("启动socket监听")

        while True:
            client, addr = await self.loop.sock_accept(server)  
            self.startNewTask(self.startClient(client, addr))

    def startNewTask(self,future):
        #通过当前线程开启新的线程去启动事件循环
        new_loop = asyncio.new_event_loop()
        threading.Thread(target=new_loop.run_until_complete,args=(future,)).start()

    async def sendcmdSync(self, cmd):
        t = self.loop.create_task(self.hassclient.send_command(cmd))
        while not t.done():
            await asyncio.sleep(0)
        return t.result()

    async def getAPIData(self,path):
        _LOGGER.info("收到api请求:" + path)
        if path.startswith("lovelace"):
            t = await self.sendcmdSync({"type": "lovelace/config", "url_path": path})
            
            return json.dumps(t,ensure_ascii=False)
        return ""


    async def startClient(self, conn, addr):
        curloop = asyncio.get_event_loop()
        self.clientList[conn] = curloop
        with conn:
            _LOGGER.info("客户端连接进入%s" % str(addr))
            try:
                while conn:
                    data = await curloop.sock_recv(conn, 10240)
                    if data:
                        data = data.decode('utf8')
                        _LOGGER.debug("收到屏指令：%s" % data)
                        if data.startswith("GET"):
                            dt = await self.getAPIData(data.split('\r')[0][3:][:-8].strip()[1:])
                            strtt = 'HTTP/1.1 200 OK\r\n\r\n %s' % dt
                            conn.send(strtt.encode('utf8'))
                            conn.close()
                            break # 单次连接，断开连接后直接结束
                        if data.startswith("GETStatus"):
                            dt = await self.getAPIData(data.split('\r')[0][3:][:-8].strip()[1:])
                            strtt = 'HTTP/1.1 200 OK\r\n\r\n %s' % dt
                            conn.send(strtt.encode('utf8'))
                            conn.close()
                            break # 单次连接，断开连接后直接结束
                        self.loop.create_task(self.hassclient.send_command(json.loads(data)))
            except socket.error as e:
                _LOGGER.error('socket Receive error:' + str(e))

        if conn in self.clientList.keys():
            self.clientList.pop(conn)

    async def receiveHassMsg(self, data):
        if "result" in data:
            if "views" in data["result"]: #查询了界面信息，返查状态
                for item in data["result"]["views"]:
                    for card in item["cards"]:
                        entity = card["entity"]
                        if card["type"] =="weather-forecast":
                            card["state"] = self.hassclient.get_attribute(entity)
                            card["state"]["state"] = self.hassclient.get_state(entity)
                        else:
                            card["state"] = self.hassclient.get_state(entity)
                # print(json.dumps(data["result"],ensure_ascii=False))
                data["date"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 

        #收到hass消息发送至客户端
        dt = json.dumps(data)#{'type': type, 'data': data})
        _LOGGER.debug("sendto screen[%d]:"%len(self.clientList))
        for client in self.clientList.keys():
            try:
                await self.clientList[client].sock_sendall(client, dt.encode('utf8'))
            except socket.error as e:
                _LOGGER.error('socket Send error:' + str(e))
                client.close()
                if client in self.clientList.keys():
                    self.clientList.pop(client)
        _LOGGER.debug("sendto OK")


async def main():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler('log.log'),logging.StreamHandler()])

    svr = SocketServer(8082)
    await svr.start()


if __name__ == '__main__':
    asyncio.run(main())
