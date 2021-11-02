# import ptvsd
# ptvsd.enable_attach(address = ('192.168.3.166', 5678))
# ptvsd.wait_for_attach()


from __future__ import annotations
import ai.AIModel as AIModel
from backend import DataView
import frontpage
from webFrame.webapp import webapp
import os
from hassclient import HomeAssistantClient
from myVoice import myVoice
import myVoice as vvvv
import signal
import asyncio
import imp
import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

_LOGGER = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

interrupted = False


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted


async def detect(v):
    v.playVoice("在呢")
    # print("listing...")
    # vl = myVoice()
    # print(vl.getVoice())
    print("OK")


async def rcbk(v, tmp):
    ret = v.getVoice(tmp)
    print("--->", ret)

    if "开灯" in ret:
        dt = {"type": "call_service", "domain": "switch", "service": "turn_on", "service_data": {"entity_id": "switch.testled"}, "id": 5}
        await v.hassclient.send_command(dt)
    if "关灯" in ret or "谁" in ret:
        dt = {"type": "call_service", "domain": "switch", "service": "turn_off", "service_data": {"entity_id": "switch.testled"}, "id": 5}
        await v.hassclient.send_command(dt)

    v.playVoice("处理完成")


url = "http://192.168.3.168:8123"
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJlMzJkYmVjMTI4MTk0ZDAxODk1MDY2YTA0MWQ1NDNjNCIsImlhdCI6MTYzMDExODgyNCwiZXhwIjoxOTQ1NDc4ODI0fQ.aBRaWzvHyKixnX1MiCu3uqZ4W2De44n6TynsSjUY1DY"
rooturlpath = "lovelace-wx"


async def main():
    hassclient = HomeAssistantClient(url, token)
    v = myVoice()
    v.playVoice("你好,准备接受你的指令")
    v.hassclient = hassclient
    await hassclient.connect()
    logger.info("连着至HASS")

    model = "./snowboy/小度.pmdl"

    await v.runcheck(model, detected_callback=detect, sensitivity="0.6",
                     audio_recorder_callback=rcbk, interrupt_check=interrupt_callback)

    # _stopped = asyncio.Event()
    # await _stopped.wait()

# import ai.AIModel.AIModel as AIModel


async def main2():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    _LOGGER.info("启动服务，当前路径：" + dir_path)
    rootpath = dir_path + "/webpage"

    app = webapp(82, "test")

    app.register_view(DataView(app))
    #await AIModel.async_setup(app, dir_path)
    await frontpage.async_setup(app, rootpath)
    await vvvv.async_setup(app)

    await app.start()

    _stopped = asyncio.Event()
    await _stopped.wait()
    await app.stop()


if __name__ == '__main__':
    logger.info("hello")
    # signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main2())
