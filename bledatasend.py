# -*- coding: utf-8 -*-
"""
Notifications
-------------
Example showing how to add notifications to a characteristic and handle the responses.
Updated on 2019-07-03 by hbldh <henrik.blidh@gmail.com>
"""
import datetime
import logging
import asyncio
import platform

import binascii
import threading
import time

from bleak import BleakClient
from bleak import _logger as logger
from bleak import discover
import queue
import json
# from pythonosc.udp_client import SimpleUDPClient
# from websocketServerTest import glQueue
from data_transfer import DataSend

glQueue = queue.Queue(maxsize=5000)
dataqueue = queue.Queue(maxsize=5000)


def findBlooth(dataqueue_test):
    newloop = asyncio.new_event_loop()
    asyncio.set_event_loop(newloop)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(findHardware(dataqueue_test))

    # loop=asyncio.get_event_loop()
    # loop.run_until_complete(findHardware())


async def findHardware(dataqueue_test):
    devices = await discover()
    ret = []
    for d in devices:
        if d.name.startswith('Brain') or d.name.startswith('BRAIN'):
            ret.append(d.name + ';' + d.address)
            print(d.address)
    bloothsend = DataSend(1, ret)
    finBloothStr = json.dumps(bloothsend, default=lambda obj: obj.__dict__, sort_keys=True)
    dataqueue_test.put(finBloothStr)
    print(dataqueue_test.empty())
    # dataqueue.put('findstrtes')


CHARACTERISTIC_UUID_READ_1GENERATION = (
    "2d30c082-f39f-4ce6-923f-3484ea480596"
)  # <--- Change to the characteristic you want to enable notifications from. 2d30c082-f39f-4ce6-923f-3484ea480596
CHARACTERISTIC_UUID_WRITE_1GENERATION = (
    "2d30c083-f39f-4ce6-923f-3484ea480596"
)  # <--- Change to the characteristic you want to enable notifications from. 2d30c082-f39f-4ce6-923f-3484ea480596
CHARACTERISTIC_UUID_READ_2GENERATION = (
    "0000ffe1-0000-1000-8000-00805f9b34fb"
)
CHARACTERISTIC_UUID_WRITE_2GENERATION = (
    "0000ffe3-0000-1000-8000-00805f9b34fb"
)


# client=SimpleUDPClient('127.0.0.1',1337)

def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    # print(len(data))
    # print("Received data: %s" % binascii.hexlify(data))
    glQueue.put(data)

    # client.send_message("/filter1",data)


async def run(address, loop, debug=False, socket_connect_sta=None, type=1,dataqueue_test=None):
    global bleconnect_status
    if debug:
        import sys

        # loop.set_debug(True)
        l = logging.getLogger("asyncio")
        l.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        l.addHandler(h)
        logger.addHandler(h)
    try:
        async with BleakClient(address, loop=loop) as client:

            bleconnect_status = True
            x = await client.is_connected()
            print(x)
            logger.info("Connected: {0}".format(x))
            # await client.write_gatt_char('2d30c083-f39f-4ce6-923f-3484ea480596', binascii.a2b_hex('62'))
            if type == 1:
                CHARACTERISTIC_UUID_READ = CHARACTERISTIC_UUID_READ_1GENERATION
                CHARACTERISTIC_UUID_WRITE = CHARACTERISTIC_UUID_WRITE_1GENERATION
            if type == 2 or type==3:
                CHARACTERISTIC_UUID_READ = CHARACTERISTIC_UUID_READ_2GENERATION
                CHARACTERISTIC_UUID_WRITE = CHARACTERISTIC_UUID_WRITE_2GENERATION
            await client.start_notify(CHARACTERISTIC_UUID_READ, notification_handler)
            if type==2:
                await client.write_gatt_char(CHARACTERISTIC_UUID_WRITE, binascii.a2b_hex('43'))
                # await asyncio.sleep(1.0, loop=loop)
                await client.write_gatt_char(CHARACTERISTIC_UUID_WRITE, binascii.a2b_hex('62'))
            elif type==3:
                s3 = 'AHB+START=0'
                s4 = 'AHB+MODE=2'
                s5 = 'AHB+START=1'
                await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bytes(s3,encoding="utf8"))
                time.sleep(0.1)
                await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bytes(s4,encoding="utf8"))
                time.sleep(0.1)
                await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bytes(s5,encoding="utf8"))
            # await client.write_gatt_char('2d30c083-f39f-4ce6-923f-3484ea480596', binascii.a2b_hex('62')) #2d30c083-f39f-4ce6-923f-3484ea480596
            # await client.write_gatt_char('2d30c083-f39f-4ce6-923f-3484ea480596', binascii.a2b_hex('43'))
            connect_obj=DataSend(0,'success')
            connect_obj_str=json.dumps(connect_obj, default=lambda obj: obj.__dict__, sort_keys=True)
            dataqueue_test.put(connect_obj_str)
            blestatus_number = 0
            while True:
                if socket_connect_sta.command==2:
                    # await client.write_gatt_char(CHARACTERISTIC_UUID_WRITE, binascii.a2b_hex('62'))
                    if type==3:
                        s3 = 'AHB+START=0'
                        s4 = 'AHB+MODE=3'
                        s5 = 'AHB+START=1'
                        await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bytes(s3, encoding="utf8"))
                        time.sleep(0.1)
                        await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bytes(s4, encoding="utf8"))
                        time.sleep(0.1)
                        await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bytes(s5, encoding="utf8"))
                    socket_connect_sta.command=3
                if socket_connect_sta.command==5:
                    await client.stop_notify(CHARACTERISTIC_UUID_READ)
                    break
                blestats = await client.is_connected()
                if blestats == False:
                    blestatus_number = blestatus_number + 1
                if blestatus_number >= 2 or socket_connect_sta.connect == False:
                    if blestatus_number >= 2:
                        socket_connect_sta.ble_is_alive = False
                        error_ret_obj = DataSend(1008, "蓝牙断开连接")
                        error_ret_str = json.dumps(error_ret_obj, default=lambda obj: obj.__dict__, sort_keys=True)
                        dataqueue_test.put(error_ret_str)
                    bleconnect_status = False
                    await client.stop_notify(CHARACTERISTIC_UUID_READ)
                    # await client.disconnect()
                    break
                await asyncio.sleep(0.5, loop=loop)
                # await client.write_gatt_char('2d30c083-f39f-4ce6-923f-3484ea480596', binascii.a2b_hex('43'))
            # await client.stop_notify(CHARACTERISTIC_UUID_READ)
    except Exception as e:
        print(e)


def connect(imei, socket_connect_sta, filter_para, type,dataqueue_test):
    from data_analysis import dataAnalysis
    datathread = threading.Thread(target=dataAnalysis, args=(socket_connect_sta, filter_para, type,dataqueue_test))
    datathread.setDaemon(True)
    datathread.start()
    address = (
        imei  # <--- BC:DD:C2:C9:12:22Change to your device's address here if you are using Windows or Linux
        if platform.system() != "Darwin"
        else imei  # <--- Change to your device's address here if you are using macOS
    )

    newloop = asyncio.new_event_loop()
    asyncio.set_event_loop(newloop)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(address, loop, True, socket_connect_sta, type,dataqueue_test))


if __name__ == "__main__":
    import os

    print(str)

    os.environ["PYTHONASYNCIODEBUG"] = str(1)
    address = (
        "BC:DD:C2:C9:12:22"  # <--- BC:DD:C2:C9:12:22Change to your device's address here if you are using Windows or Linux
        if platform.system() != "Darwin"
        else "243E23AE-4A99-406C-B317-18F1BD7B4CBE"
        # <--- Change to your device's address here if you are using macOS
    )
    print(address)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(address, loop, True, 'test'))
