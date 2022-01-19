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

from converterGen3 import gen3SamplesGenerate
from data_utils import ZipUtil

CHARACTERISTIC_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # <--- Change to the characteristic you want to enable notifications from.
file_name = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
unpacking_record=b''
data_lenth=0
file=open(os.getcwd() + '\\data' + '\\' + file_name + '.txt', "w")
def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    print("Received data: %s" % binascii.hexlify(data))
    print("Received data lenth: %s" % len(data))
    # file.write(datetime.now().strftime('%H-%M-%S.%f') + ':' + (binascii.hexlify(data)).decode() + '\n')
    global unpacking_record
    unpacking_record = unpacking_record + data
    if len(unpacking_record) >= 130:
        array_data = unpacking_record.split(b'##>')
        for i in range(len(array_data) - 1):
            data_satellite, str_insert, sample = gen3SamplesGenerate(array_data[i])
            file.write(datetime.now().strftime('%H-%M-%S.%f')+','+str_insert+'\n')
        unpacking_record = array_data[len(array_data) - 1]
    # global data_lenth
    # data_lenth = data_lenth + len(data)
    # timestr=datetime.now().strftime('%H-%M-%S.%f')
    # print("Received data total_lenth: %s" % data_lenth+'---'+timestr)
    # file.write(timestr + ': ' + (str(data_lenth)) + '\n')

    # if len(unpacking_record) >= 130:
    #     count = int(len(unpacking_record) / 130)
    #     for i in range(count):
    #         file.write(datetime.now().strftime('%H-%M-%S.%f') + ':' + (
    #             binascii.hexlify(unpacking_record[i * 130:130 * (i + 1)])).decode() + '\n')
    #     unpacking_record = unpacking_record[130 * (count):]

        # print(unpacking_record)
        # print('start----------find---------')
        # print('unpacking_record_lenth:%s'%len(unpacking_record))
        # bgn = unpacking_record.find(b'##>')
        # # print('bgn--------------position:%s'%bgn)
        # # print('unpacking_record_bgn_lenth:%s' % len(unpacking_record[bgn:]))
        # if len(unpacking_record[bgn:]) >= 130:
        #     print('start----------analysis------------')
        #     analysis_data = unpacking_record[bgn:(130 + bgn)]
        #     file.write(datetime.now().strftime('%H-%M-%S.%f')+':'+(binascii.hexlify(analysis_data)).decode() + '\n')
        #     print("Received analysis_data: %s" % binascii.hexlify(analysis_data))
        #     print("Received analysis_data lenth: %s" % len(analysis_data))
        #     unpacking_record = unpacking_record[130 + bgn:]

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
        # t=int(time.time())
        # print(t)
        # s1='AHB+TIME=' +str(t)
        # s2='AHB+UUID=test'
        s3='AHB+MODE=1'
        s4='AHB+START=1'
        s5 = 'AHB+START=0'
        # s6 = 'AHB+START=1'
        # bs1=bytes(s1, encoding="utf8")
        # bs2=bytes(s2,encoding="utf8")
        bs3=bytes(s3,encoding="utf8")
        bs4=bytes(s4,encoding="utf8")
        bs5 = bytes(s5, encoding="utf8")
        # bs6=bytes(s6,encoding="utf8")
        # await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bs1)
        # time.sleep(0.1)
        # await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bs2)
        # time.sleep(0.1)
        await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bs5)
        time.sleep(0.1)
        await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bs3)
        time.sleep(0.1)

        await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bs4)

        # await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bytes('AHB+START=1',encoding="utf8"))
        blestatus_number = 0
        while True:
            blestats = await client.is_connected()
            # await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bs1)
            # time.sleep(0.1)
            # await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bs2)
            # time.sleep(0.1)
            # await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bs3)
            # time.sleep(0.1)
            # await client.write_gatt_char('0000ffe3-0000-1000-8000-00805f9b34fb', bs4)
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
        "3C:A5:51:85:5F:A5"  # <--- 3C:A5:4A:DE:EF:E5 Change to your device's address here if you are using Windows or Linux
        if platform.system() != "Darwin"
        else "E678F987-58E2-434B-BC01-C2E2624F510C"  # <--- Change to your device's address here if you are using macOS
    )
    loop = asyncio.get_event_loop()
    # loop.set_debug(True)
    loop.run_until_complete(run(address, True))