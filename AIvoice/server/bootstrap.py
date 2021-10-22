
from __future__ import annotations
import asyncio
import logging

from webFrame.webapp import webapp
import frontpage
import backend
import os 
_LOGGER = logging.getLogger(__name__)



async def main2():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    _LOGGER.info("启动服务，当前路径：" + dir_path)
    rootpath = dir_path + "/webpage/"

    app = webapp(82,"test")

    await backend.async_setup(app)
    await frontpage.async_setup(app,rootpath)

    await app.start()
    
    _stopped = asyncio.Event()
    await _stopped.wait()
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    asyncio.run(main2())