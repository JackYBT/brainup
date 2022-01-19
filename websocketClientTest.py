import asyncio
import websockets
import time
import numpy as np

async def hello(uri):
    async with websockets.connect(uri,max_size=10*1024*1024) as websocket:
        # await websocket.send("Hello world!")
        # messagetest=await websocket.recv()
        # print(messagetest)
        # await websocket.send("{\"file_url\": \"https://naolu-log.oss-cn-beijing.aliyuncs.com/whole_hat/8/2020-12-07_15-57-05.edf\", \"id\": 7, \"notch_filter\": 1, \"filter_param\": 1}")

        # step 1
        await websocket.send("{\"id\": 1}")

        # step 2
        await websocket.send("{\"address\": \"3CA551855EF6\", \"id\": 2}")

        flag=1
        while True:
            message=await websocket.recv()
            print(message)
            # await websocket.send("{\"address\": \"3C:A5:4A:DF:26:9F\", \"id\": 3}")

            # await websocket.send('test')
            # if(flag==1):
            #     await websocket.send("{\"address\": \"BC:DD:C2:C9:12:22\", \"id\": 2}")
            #     print('address\": \"BC:DD:C2:C9:12:22\", \"id\": 2}')
            #     flag=2

            # i=i+1
            # timeStr=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            # await websocket.send(timeStr+timeStr)
            # time.sleep(180)
if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(
        hello('ws://127.0.0.1:8765'))

