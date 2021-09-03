"""
微信后台服务入口
"""
from __future__ import annotations
import asyncio
import logging

from webFrame.webapp import webapp
import weixinMgr.frontpage as frontpage
import weixinMgr.backend as backend
from weixinMgr.wxManage import wxManage
import os
from hassclient import HomeAssistantClient
from weixinMgr.wxUserManage import WxUserManage

_LOGGER = logging.getLogger(__name__)

def genWcCmd(app):
    async def WxCommand(msg):
        _LOGGER.info("收到微信指令："+ msg)
        if "开灯" in msg:
            dt = {"type":"call_service","domain":"switch","service":"turn_on","service_data":{"entity_id":"switch.testled"},"id":5}
            await app.hassclient.send_command(dt)
            return "OK"
        if "关灯" in msg or "谁" in msg:
            dt = {"type": "call_service", "domain": "switch", "service": "turn_off", "service_data": {"entity_id": "switch.testled"}, "id": 5}
            await app.hassclient.send_command(dt)
            return "OK"
        return "您的指令未能识别"
    return WxCommand

# url = "http://127.0.0.1:8123"
# token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiI3MTcwMmZiZmViNWU0YjdhYjVjZmY2M2Q3OTIyMDgwMiIsImlhdCI6MTYzMDM5MjU1MCwiZXhwIjoxOTQ1NzUyNTUwfQ.ZswvRMp5QynvXflNSYIvp7zZbbujylxl4S1xm-_s4Tw"
# rooturlpath = None

url = "http://192.168.3.168:8123"
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJlMzJkYmVjMTI4MTk0ZDAxODk1MDY2YTA0MWQ1NDNjNCIsImlhdCI6MTYzMDExODgyNCwiZXhwIjoxOTQ1NDc4ODI0fQ.aBRaWzvHyKixnX1MiCu3uqZ4W2De44n6TynsSjUY1DY"
rooturlpath ="lovelace-wx"


async def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    _LOGGER.info("启动服务，当前路径：" + dir_path)

    app = webapp(82, "MyWx")
    app.rootPath = dir_path
    app.userMgr = WxUserManage(app)
    app.wxManage = wxManage()
    app.rooturlpath = rooturlpath

    app.hassclient = HomeAssistantClient(url, token)
    await app.hassclient.connect()
    _LOGGER.info("连着至HASS")

    await backend.async_setup(app, genWcCmd(app))
    await frontpage.async_setup(app, dir_path + "/webpage/")

    await app.start()

    _stopped = asyncio.Event()
    await _stopped.wait()

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler('log.log'),logging.StreamHandler()])

    asyncio.run(main())
