# import ptvsd
# ptvsd.enable_attach(address = ('192.168.3.166', 5678))
# ptvsd.wait_for_attach()


from __future__ import annotations
import imp
import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

import asyncio
import signal
from myVoice import myVoice
from hassclient import HomeAssistantClient
import os

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


async def rcbk(v,tmp):
    ret = v.getVoice(tmp)
    print("--->", ret)
    
    if "开灯" in ret:
        dt = {"type":"call_service","domain":"switch","service":"turn_on","service_data":{"entity_id":"switch.testled"},"id":5}
        await v.hassclient.send_command(dt)
    if "关灯" in ret or "谁" in ret:
        dt = {"type": "call_service", "domain": "switch", "service": "turn_off", "service_data": {"entity_id": "switch.testled"}, "id": 5}
        await v.hassclient.send_command(dt)

    v.playVoice("处理完成")


url = "http://192.168.3.168:8123"
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJlMzJkYmVjMTI4MTk0ZDAxODk1MDY2YTA0MWQ1NDNjNCIsImlhdCI6MTYzMDExODgyNCwiZXhwIjoxOTQ1NDc4ODI0fQ.aBRaWzvHyKixnX1MiCu3uqZ4W2De44n6TynsSjUY1DY"
rooturlpath ="lovelace-wx"

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
from ai.AIModel import AIModel


if __name__ == '__main__':
    logger.info("hello")
    # signal.signal(signal.SIGINT, signal_handler)
    # asyncio.run(main())

    rootPath = os.path.split(os.path.realpath(__file__))[0]
    mode = AIModel(rootPath)
    mode.train()
    logger.info("训练完成")

    # mode.loadModel()
    # from flask import Flask
    # app = Flask(__name__)
    # from flask_cors import CORS
    # # 跨域设置
    # CORS(app)
    # # 绑定路由
    # app.add_url_rule("/nlu/predict", None, getattr(mode, "predict"),methods=["POST"])

    # # 启动服务
    # app.run(host='0.0.0.0', port=9042, debug=False)
