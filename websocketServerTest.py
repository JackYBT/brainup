import asyncio

import atexit
import binascii
import multiprocessing
import sys
import traceback

import websockets
import queue
import json
import threading
import time

import os

from datetime import datetime

import configure
import serialUtil
from serialUtil import findBlooth, openBluetooth, bleconnect_status, switch_blooth


from data_transfer import DataSend, handle, DataReceive
from file_analysis import file_filter, data_dump
from socket_connect_status import SocketConnectStatus, FilterParams

config = configure.getConfig()

glQueue = queue.Queue(maxsize=5000)
dataqueue_test = queue.Queue(maxsize=5000)

async def echo(websocket, path):
    global glQueue
    global dataqueue_test

    glQueue.queue.clear()
    dataqueue_test.queue.clear()
    socket_connect_sta = SocketConnectStatus(status=True)
    filter_para = FilterParams(filter_param=1, draw_number=1)
    consumer_task = asyncio.ensure_future(
        consumer_handler(websocket, path, socket_connect_sta, filter_para,dataqueue_test,glQueue))
    producer_task = asyncio.ensure_future(
        producer_handler(websocket, path, socket_connect_sta,dataqueue_test))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
    )
    for task in pending:
        task.cancel()

async def consumer_handler(websocket, path, socket_connect_sta, filter_para, dataqueue_test, glQueue):
    global bleconnect_status
    while True:
        try:
            message = await websocket.recv()
            print(message)
            receivedata = json.loads(message, object_hook=DataReceive)
            if receivedata.id == 201:
                switch_blooth_thread = threading.Thread(target=switch_blooth, 
                    args=(receivedata.address, receivedata.type, filter_para, socket_connect_sta, dataqueue_test, glQueue))
                switch_blooth_thread.setDaemon(True)
                switch_blooth_thread.start()

            if receivedata.id == 1:

                # 1、阻抗 2、开始脑波数据 3、脑波数据发送中 5、结束采集上传数据
                socket_connect_sta.command = 1
                # userName = 'test'
                if hasattr(receivedata,'name'):
                    userName = receivedata.name
                filter_para.user_name = "Hello"#userName
                # userMode = 'H001'
                if hasattr(receivedata,'mode'):
                    userMode = receivedata.mode
                filter_para.user_mode = userMode
                
                if hasattr(receivedata,'number'):
                    userNumber = receivedata.number
                    filter_para.user_number = userNumber
                else:
                    filter_para.user_number = "unknown"

                filter_para.start_record = False
                filter_para.test_start_record = False
                filter_para.satellite_status = True
                filter_para.write_eeg_header = False

                receivedata.phbFatherDefault = None

                findblooththread = threading.Thread(target=findBlooth, args=(dataqueue_test,filter_para,socket_connect_sta,glQueue,receivedata.phbFatherDefault))
                findblooththread.setDaemon(True)
                findblooththread.start()
                # new_process = multiprocessing.Process(target=findBlooth, args=(dataqueue_test,))
                # new_process.start()
            if receivedata.id == 2:
                #receivedata.phbFatherDefault = 8
                if bleconnect_status == False:

                    imei = receivedata.address
                    type = receivedata.type
                    # filter_para.draw_number = receivedata.draw_number

                    print("imei:",imei)

                    tblutooth = threading.Thread(target=openBluetooth, args=(imei, type, socket_connect_sta, glQueue, dataqueue_test, receivedata.phbFatherDefault))
                    # t = threading.Thread(target=nacosStart, args=('192.168.1.124', 8080, message))
                    tblutooth.setDaemon(True)
                    tblutooth.start()

                else:
                    print("蓝牙设备已连接")
                    error_ret_obj = DataSend(1010, "蓝牙设备已连接！")
                    error_ret_str = json.dumps(error_ret_obj, default=lambda obj: obj.__dict__, sort_keys=True)
                    dataqueue_test.put(error_ret_str)

            if receivedata.id == 31:
                filter_para.test_start_record = True
                #filter_para.start_record = True
            if receivedata.id == 3:
                # filter_para.save_id = '1234'
                if hasattr(receivedata,'save_id'):
                    filter_para.save_id = receivedata.save_id

                filter_para.save_file_path = filter_para.file_path + '/' + filter_para.file_name + '_' +str(filter_para.save_id)
                filter_para.save_file = open(filter_para.save_file_path + '.txt', "w")

                filter_para.start_record = True
                filter_para.write_eeg_header = True
                socket_connect_sta.command = 2
                glQueue.queue.clear()
                dataqueue_test.queue.clear()
                serialUtil.openDataReceive(serialUtil.mode["filter"])
            if receivedata.id == 4:
                filter_para.filter_param = receivedata.filter
                # filter_param = receivedata.filter
                print('------------receivefilter_param--------' + str(filter_para.filter_param))
            if receivedata.id==5:
                filter_para.notch_filter=receivedata.notch_filter
                print('------------receive notch filter_param--------' + str(filter_para.filter_param))
            if receivedata.id == 6:

                filter_para.save_action = True
                serialUtil.closeDataReceive()

            if receivedata.id == 7:
                file_url=receivedata.file_url
                page_size=int(receivedata.page_size)
                page_number=int(receivedata.page_number)
                vertical_size=int(receivedata.vertical_size)
                notch_filter=int(receivedata.notch_filter)
                filter_param=int(receivedata.filter_param)
                data_send_json=file_filter(file_url,notch_filter,filter_param,page_size,page_number,vertical_size)
                await websocket.send(data_send_json)

                socket_connect_sta.connect = False
                break

            if receivedata.id == 8:
                file_url = receivedata.file_url
                notch_filter=int(receivedata.notch_filter)
                # channels=receivedata.channels
                channels = '0,1,2,3,4,5'
                filter_param=int(receivedata.filter_param)
                start_time=receivedata.start_time
                vertical_size=int(receivedata.vertical_size)
                dump_json=data_dump(start_time,notch_filter,filter_param,file_url,channels,vertical_size)
                await websocket.send(dump_json)

                socket_connect_sta.connect = False
                break

            if receivedata.id == 60:
                filter_para.draw_number = receivedata.draw_number
                print('------------receivefilter_param--------' + str(filter_para.draw_number))

        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("接收主程序处理异常,print_exception:")
            traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)

            print('exitlink-------')
            serialUtil.closeDataReceive()

            socket_connect_sta.connect = False
            await websocket.close(reason="user exit")
            break
    if socket_connect_sta.connect == False:
        print("关闭连接-consumer")
        await websocket.close()


async def producer_handler(websocket, path, socket_connect_sta, dataqueue_test):
    while True:
        if socket_connect_sta.connect == False:
            serialUtil.closeDataReceive()
            break
        if dataqueue_test.empty() == False:
            message = dataqueue_test.get(block=False)
            # print('semdessage'+message)
            try:
                await websocket.send(message)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print("发送主程序处理异常,print_exception:")
                traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)

                serialUtil.closeDataReceive()
                socket_connect_sta.connect = False
                print('jump-send-circle--because--end-except')
                await websocket.close(reason="user exit")
                break
        else:
            if socket_connect_sta.ble_is_alive == False:
                print('jump-send-circle-because-bleisalive false-----------')
                serialUtil.closeDataReceive()
                socket_connect_sta.connect = False
                await websocket.close(reason="user exit")
                break
        await asyncio.sleep(0.001)

    if socket_connect_sta.connect == False:
        print("关闭连接-producer")
        await websocket.close()

atexit.register(serialUtil.closeLocalSerial)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(
        websockets.serve(echo, config['server_ip'], config['server_port']))
    asyncio.get_event_loop().run_forever()
