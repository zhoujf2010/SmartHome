# import ptvsd
# ptvsd.enable_attach(address = ('192.168.3.166', 5678))
# ptvsd.wait_for_attach()


from __future__ import annotations
import ai.AIModel as AIModel
import backend
import frontpage
from webFrame.webapp import webapp
from webFrame.eventBus import EventBus
import os
import hassclient
import myVoice
import signal
import asyncio
import imp
import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)

interrupted = False


def signal_handler(signal, frame):
    global interrupted
    interrupted = True


def interrupt_callback():
    global interrupted
    return interrupted


async def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    logger.info("启动服务，当前路径：" + dir_path)
    rootpath = dir_path + "/webpage"

    app = webapp(8082, "test")
    app.eventBus = EventBus()
    app.loop = asyncio.get_running_loop()

    # await backend.async_setup(app)
    # await frontpage.async_setup(app, rootpath)
    # await AIModel.async_setup(app, dir_path)
    await myVoice.async_setup(app)
    # await hassclient.async_setup(app)

    await app.start()

    _stopped = asyncio.Event()
    await _stopped.wait()
    await app.stop()


if __name__ == '__main__':
    logger.info("hello")
    # signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())
