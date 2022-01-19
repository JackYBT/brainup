# -*- coding: utf-8 -*-
"""
Notifications
-------------
Example showing how to add notifications to a characteristic and handle the responses.
Updated on 2019-07-03 by hbldh <henrik.blidh@gmail.com>
"""
import logging
import asyncio
import platform
import binascii
import time

import oss2
from bleak import BleakClient
from bleak import _logger as logger
from datetime import datetime
import os
from data_utils import ZipUtil

CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # <--- Change to the characteristic you want to enable notifications from.

file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
file=open(os.getcwd() + '\\data' + '\\' + file_name + '.txt', "w")
unpacking_record=b''
data_lenth=0
def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    global unpacking_record
    unpacking_record=unpacking_record+data
    # global data_lenth
    # data_lenth = data_lenth + len(data)
    # if len(unpacking_record) >= 128:
    #
    #     count=int(len(unpacking_record)/128)
    #     for i in range(count):
    #         file.write(datetime.now().strftime('%H-%M-%S.%f') + ':' + (binascii.hexlify(unpacking_record[i*128:128*(i+1)])).decode() + '\n')
    #     unpacking_record = unpacking_record[128 * (count):]
    if len(unpacking_record) >= 128:
        array_data=unpacking_record.split(b'\n\xff')
        for i in range(len(array_data)-1):
            # if len(array_data[i]<127):
            #
            file.write(datetime.now().strftime('%H-%M-%S.%f') +':'+ (binascii.hexlify(array_data[i])).decode() + '\n')
        unpacking_record=array_data[len(array_data)-1]

        # bgn = unpacking_record.find(b'\n\xff')
        # if bgn>0:
        #     analysis_data = unpacking_record[0:bgn+1]
        #     print("analysis_data: %s" % len(analysis_data))
        #     file.write(datetime.now().strftime('%H-%M-%S.%f') +':'+ (binascii.hexlify(analysis_data)).decode() + '\n')
        #     unpacking_record = unpacking_record[bgn + 1:]

    # print("Received data: %s" % binascii.hexlify(data))
    print((binascii.hexlify(data)))
    # print("Received data: %s" % binascii.hexlify(data))
    print("Received data lenth: %s"  % len(data))
    # file.write(datetime.now().strftime('%H-%M-%S.%f')+(binascii.hexlify(data)).decode()+'\n')
    # file.write(datetime.now().strftime('%H-%M-%S.%f') +': '+ (str(data_lenth)) + '\n')
    # print("Received data number: %s" %(data[1]))


async def run(address, debug=False):
    if debug:
        import sys

        l = logging.getLogger("asyncio")
        l.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        l.addHandler(h)
        logger.addHandler(h)

    async with BleakClient(address) as client:
        x = await client.is_connected()
        logger.info("Connected: {0}".format(x))

        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        # await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', binascii.a2b_hex('43'))

        await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', binascii.a2b_hex('62'))
        blestatus_number = 0
        while True:
            blestats = await client.is_connected()
            if blestats == False:
                blestatus_number = blestatus_number + 1
            if blestatus_number >= 5:
                print('------------bledisconnect--------------')
                await client.stop_notify(CHARACTERISTIC_UUID)
                await client.disconnect()
            await asyncio.sleep(1.0, loop=loop)
        await client.stop_notify(CHARACTERISTIC_UUID)

if __name__ == "__main__":
    # file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')[:-5]
    #
    # print(os.path.basename(r'D:\code\brain_hat\brain_hat\data\2020-12-04_10-30-37' + '.txt'))
    # file_name = os.path.splitext(os.path.basename(r'D:\code\brain_hat\brain_hat\data\2020-12-04_10-30-37' + '.txt'))[0]
    # for i in range(5):
    #     print(i)
    # import os
    #
    #
    #
    # file_name_test = datetime.now().strftime('%H-%M-%S.%f')
    # print(file_name_test)
    # auth = oss2.Auth('LTAI4G1LwPb2i4Cp5d3A3wUq', 'qe0FiUtWwiYSsSdTAHlYkPMvMiHXuS')
    # bucket = oss2.Bucket(auth, 'https://oss-cn-beijing.aliyuncs.com', 'naolu-log')
    # object_name = 'whole_hat'+'/'+os.path.basename(os.getcwd() + '\\data' +'\\'+'test1.zip')
    # bucket.put_object_from_file(object_name, os.getcwd() + '\\data' +'\\'+'test1.zip')
    #
    #
    # file_test=os.getcwd() + '\\data' +'\\'+'test1.txt'
    # file_split=os.path.split(file_test)
    # print(str(file_split[1]))
    # z=ZipUtil()
    # files=[os.getcwd() + '\\data' +'\\'+'test1.txt']
    # zip_file=os.getcwd() + '\\data' +'\\'+'test1.zip'
    # z.get_zip(files,zip_file)
    # file_name=datetime.now().strftime('%H-%M-%S.%f')
    # print(file_name)
    # file = open(os.getcwd() + '\\data' +'\\'+file_name+'.txt',"w")
    # file.write('test')
    # file.close()
    # os.environ["PYTHONASYNCIODEBUG"] = str(1)
    address = (
        "3C:A5:4A:DE:DB:EF"  # <--- 3C:A5:4A:DE:DB:EF Change to your device's address here if you are using Windows or Linux
        if platform.system() != "Darwin"
        else "E678F987-58E2-434B-BC01-C2E2624F510C"  # <--- Change to your device's address here if you are using macOS
    )
    loop = asyncio.get_event_loop()
    # loop.set_debug(True)
    loop.run_until_complete(run(address, True))