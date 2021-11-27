import asyncio
from asyncio.tasks import sleep
import time

async def a():
    print('Suspending a')
    await asyncio.sleep(0)
    print('Resuming a')


async def b():
    print('In b')
    time.sleep(3)
    print('In b again')

async def ttt(x):
    print("111")
    return x + 20

import asgiref

async def main():
    # tmp = a()
    # await tmp
    # # await a()
    # # await b()
    # await asyncio.gather(a(), b())
    p = ttt(5)
    print(p)

    x = await p
    print(x)

    # cc = asgiref.sync.async_to_sync(ttt)(5)
    # print(cc)

    loop = asyncio.get_event_loop()
    t = loop.create_task(ttt(5))
    while not t.done():
        await asyncio.sleep(0)

    # txx.
    # t = loop.run_until_complete(ttt(5))

    print(t.result())







if __name__ == '__main__':
    asyncio.run(main())
    print("end")