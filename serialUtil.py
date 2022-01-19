
import json
import sys
import traceback

import serial  # 导入模块
import time
import threading
import configure

import os
from datetime import datetime

from data_analysis import dataAnalysis
from data_transfer import DataSend


receive_status = False
bleconnect_status = False
bleconnect_dict = {}
bluetooth_list = []

mode = {"impedance": "2", "filter": "3"}   # 2：阻抗模式，3：滤波模式
hardware_type_name = {1:'BrainUp71', 5:'BrainUp70', 8:'BRAIN-AHB'}
hardware_type_channel = {1:1, 2:5, 3:8}

# 端口，GNU / Linux上的/ dev / ttyUSB0 等 或 Windows上的 COM3 等
# com_name="COM3"
# 波特率，标准值之一：50,75,110,134,150,200,300,600,1200,1800,2400,4800,9600,19200,38400,57600,115200
# bit_rate=115200
# 超时设置,None：永远等待操作，0为立即返回请求结果，其他值为等待超时时间(单位为秒）

timex = 5


def openLocalSerial():
    print("准备连接USB串口设备")
    while True:
        try:
            config = configure.getConfig()
            ser = serial.Serial(config['com_name'], config['bit_rate'], timeout=timex)
            ser.write("AT\r\n".encode("gbk"))
            ret = ser.readall()
            if ret.decode("gbk").find("OK") > -1:
                print("串口打开正常,连接状态",ret.decode("gbk"))
                if ser.is_open:
                    ser.write("AT+BAUD8\r\n".encode("gbk"))
                    time.sleep(0.2)
                    ser.write("AT+HOSTEN1\r\n".encode("gbk"))
                    time.sleep(0.2)
                    print(ser.readall().decode("gbk"))
                    print("连接串口完成，等待后续指令...")
                else:
                    print("串口未打开")
                return ser
            else:
                print("串口打开异常,连接状态", ret.decode("gbk"))
                time.sleep(3)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("打开串口异常,print_exception:")
            traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)
            print('打开串口异常，请确认USB串口设备已插入(如已插入请重新拔插)，配置文件中配置的COM口正常')
            time.sleep(3)


def closeLocalSerial():
    global localSerial
    global bleconnect_status
    global receive_status
    if localSerial.is_open:
        localSerial.close()
        bleconnect_status = False
        receive_status = False
        print("关闭串口：串口已关闭")
    else:
        print("关闭串口：已是关闭状态")

localSerial = openLocalSerial()

def closeDataReceive():
    global localSerial
    global bleconnect_status
    global receive_status
    try:
        if localSerial.is_open:
            if bleconnect_status == True:
                if bleconnect_dict["hardware_type"] in (1,2):
                    localSerial.write(b's')
                    time.sleep(0.5)
                elif bleconnect_dict["hardware_type"] == 3:
                    s1 = 'AHB+START=0'
                    s2 = 'AHB+MODE=1'  # 数据传输模式  0自校准模式,1阻抗模式,2正常测试模式
                    localSerial.write(s1.encode("utf-8"))
                    time.sleep(0.1)
                    localSerial.write(s2.encode("utf-8"))
                    time.sleep(0.1)
                print("关闭数据传输：已关闭串口蓝牙数据传输")
                receive_status = False
            else:
                print("关闭数据传输：当前连接未打开")
        else:
            print("关闭数据传输：串口未打开")

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("关闭数据接收处理异常,print_exception:")
        traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)


def openDataReceive(data_mode):
    global localSerial
    global bleconnect_status
    global receive_status
    try:
        if not localSerial.is_open:
            print("打开数据传输：串口当前已关闭，重新打开-开始")
            localSerial = openLocalSerial()
            print("打开数据传输：串口当前已关闭，重新打开-完成")
        #print("the blue tooth:", bleconnect_dict)
        if localSerial.is_open:
            if bleconnect_status == True:
                if bleconnect_dict["hardware_type"] in (1,2):
                    localSerial.write(b's')
                    time.sleep(0.5)
                    localSerial.write(b'b')
                elif bleconnect_dict["hardware_type"] == 3:
                    s0 = 'AHB+START=0'
                    s1 = 'AHB+MODE=' + data_mode # 数据传输模式  0自校准模式,2阻抗模式,3采样模式
                    s2 = 'AHB+START=1'
                    localSerial.write(s0.encode("utf-8"))
                    time.sleep(0.1)
                    localSerial.write(s1.encode("utf-8"))
                    time.sleep(0.1)
                    localSerial.write(s2.encode("utf-8"))
                    time.sleep(0.1)
                
                print("打开数据传输：已打开串口蓝牙数据传输")
                receive_status = True
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("打开数据接收处理异常,print_exception:")
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)


#检查蓝牙连接状态，当为True时为可正常接收到数据，则连接正常，否则False无法接收数据
def checkBluetoothStatus():
    global mode
    ret = True
    try:
        openDataReceive(mode["impedance"])
        data = localSerial.read(130)
        if len(data) < 50:
            ret = False
        closeDataReceive()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("检查蓝牙连接状态处理异常,print_exception:")
        traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)
    return ret

def __bluetooth_connected__(imei):
    global bluetooth_list
    for bluetooth in bluetooth_list:
        if bluetooth["device"].endswith(imei):
            bluetooth["connected"] = True
        else:
             bluetooth["connected"] = False

def openBluetooth(imei, type, socket_connect_sta, glQueue, dataqueue_test, phbFatherDefault=8):
    global localSerial
    global bleconnect_status
    global bleconnect_dict
    global mode
    global receive_status
    global bluetooth_list
    global hardware_type_channel
    try:
        if receive_status == True:
            print("正在采集数据不支持更换设备连接")
            error_ret_obj = DataSend(1010, "正在采集数据不支持更换设备连接！")
            error_ret_str = json.dumps(error_ret_obj, default=lambda obj: obj.__dict__, sort_keys=True)
            dataqueue_test.put(error_ret_str)
            return

        if localSerial.is_open:
            if checkBluetoothStatus() == False:
                s1 = "AT+CONN" + imei + "\r\n"
                localSerial.write(s1.encode("gbk"))
                # localSerial.write("AT+CONN3CA551855EF6\r\n".encode("gbk"))
                ret = localSerial.readall().decode("gbk") #.split('+')
                print(">>AT+CONN:", ret)
                for msg in [ret]:
                    if msg.find("OK") >= 0:
                        if msg.find(imei) >= 0:
                            print("串口连接蓝牙:已连接")
                            bleconnect_status = True

                            bleconnect_dict["imei"] = imei
                            bleconnect_dict["hardware_type"] = type
                            __bluetooth_connected__(imei)
                            break
                        else:
                            print("串口连接蓝牙：连接异常，请重试", msg)

            if bleconnect_status == True:
                print("串口连接蓝牙:使用已存在连接")

                closeDataReceive()
                openDataReceive(mode["impedance"])

                # here we create file - lihanhui
                imei = bleconnect_dict["imei"]
                filter_para = bleconnect_dict["filter_para"]
                date_str = datetime.now().strftime('%Y-%m-%d')
                path_str = filter_para.user_number + '_' + filter_para.user_name + '_' + configure.mode[filter_para.user_mode]+ '_' + imei[-4:]
                filePath = os.getcwd() + '/data/' + date_str + '/' + path_str
                is_exists = os.path.exists(filePath)
                if not is_exists:
                    os.makedirs(filePath)
                filter_para.file_path = filePath

                edfFilePath = os.getcwd() + '/edf/'  + date_str + '/' + filter_para.user_name
                is_exists = os.path.exists(edfFilePath)
                if not is_exists:
                    os.makedirs(edfFilePath)
                filter_para.edf_file_path = edfFilePath
                
                path_str = filter_para.user_number + '_' + filter_para.user_name + '_' + filter_para.user_mode + '_' + imei[-4:]
                imp_file_name = path_str + '_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                filter_para.file_name = imp_file_name

                filter_para.imp_save_file = open(filter_para.file_path + '/' + filter_para.file_name + '_imp.txt', 'w')
                #====================================
                connect_obj = DataSend(0, {'status':'success','imei':bleconnect_dict["imei"],'type':bleconnect_dict["hardware_type"], 'channels': hardware_type_channel[bleconnect_dict["hardware_type"]]})
                #connect_obj = DataSend(0, 'success')
                connect_obj_str = json.dumps(connect_obj, default=lambda obj: obj.__dict__, sort_keys=True)
                # print("connect_obj_str:" ,connect_obj_str)
                dataqueue_test.put(connect_obj_str)

                filter_para.hardware_type = type

                receive = threading.Thread(target=receiveData, args=(glQueue,socket_connect_sta,dataqueue_test))
                receive.setDaemon(True)
                receive.start()

                datathread = threading.Thread(target=dataAnalysis,
                                              args=(socket_connect_sta,filter_para, type, dataqueue_test,glQueue))
                datathread.setDaemon(True)
                datathread.start()

        else:
            print("串口连接蓝牙:串口未打开")
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("连接蓝牙处理异常,print_exception:")
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)


def closeBluetooth():
    global localSerial
    # 目前串口连接的蓝牙设备不支持单独关闭

def receiveData(glQueue, socket_connect_sta, dataqueue_test):
    global localSerial
    global bleconnect_status
    global bleconnect_dict
    global receive_status
    if localSerial.is_open:
        unpacking_record = 0x00
        numbers = 0
        while True:
            try:
                size = 130
                if bleconnect_dict["hardware_type"] in (1, 2):
                    size = 85
                # if localSerial.in_waiting > size:
                #     size = localSerial.in_waiting
                data = localSerial.read(size)

                # data = b''
                # while datas.rfind(b'##>') > 0:
                #     data += datas[datas.rfind(b'##>'):]
                #     datas = datas[0:datas.rfind(b'##>')]
                # data += datas

                if len(data) > 10 and len(data) < 20 and data.decode('gbk').find("DISCONNECTED") > -1:
                    print("接收蓝牙数据：连接中断")
                    error_ret_obj = DataSend(1008, "蓝牙断开连接")
                    error_ret_str = json.dumps(error_ret_obj, default=lambda obj: obj.__dict__, sort_keys=True)
                    dataqueue_test.put(error_ret_str)

                    bleconnect_status = False
                    socket_connect_sta.ble_is_alive = False

                    break
                if receive_status == True :
                    if len(data) > 0:
                        # print("data>>",b'##>' +data)
                        numbers = numbers + 1
                        if numbers % 100 == 0:
                            print(glQueue.qsize())
                        glQueue.put(data)
                else:
                    print("接收蓝牙数据：已关闭数据接收")
                    break
                if socket_connect_sta.connect == False:
                    print("接收蓝牙数据：客户端连接已断开，结束接收数据")
                    break

            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print("接收数据处理异常,print_exception:")
                traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)

def findHardware(dataqueue_test, phbFatherDefault):
    global localSerial
    global bluetooth_list
    try:
        if not localSerial.is_open:
            print("串口已关闭，准备重新打开")
            localSerial = openLocalSerial()
        else:
            print("串口已打开")

        devices = {}
        result = localSerial.write("AT+SCAN\r\n".encode("gbk"))
        time.sleep(0.2)
        deviceInfo = localSerial.readall()
        print("phbFatherDefault:", phbFatherDefault)
        print("查询设备信息:", deviceInfo)
        deviceName = str(deviceInfo.replace(b'\r\n', b'').replace(b'\x00', b'')).split('+')
        for nm in deviceName:
            try:
                # nm = str(nm.replace(b'\r\n', b''), encoding="utf-8")
                if nm.find('Brain') > 0 or nm.find('BRAIN') > 0:
                    print("Brain Device Info:", nm)
                    device = nm[6:].split(',')
                    print(">>", device[2] + ';' + device[0])
                    if (not phbFatherDefault or phbFatherDefault == 8) and device[2].find(hardware_type_name[8]) >-1 and not device[2].endswith("OK"):
                        devices[device[2] + ';' + device[0]] = 8
                    if (not phbFatherDefault or phbFatherDefault == 5) and device[2].find(hardware_type_name[5]) >-1 and not device[2].endswith("OK"):
                        devices[device[2] + ';' + device[0]] = 5
                    if (not phbFatherDefault or phbFatherDefault == 1) and device[2].find(hardware_type_name[1]) >-1 and not device[2].endswith("OK"):
                        devices[device[2] + ';' + device[0]] = 1
            except Exception as deviceNameEx:
                print(deviceNameEx)
        datas = []        
        for device, channels in devices.items():
              datas.append({"device": device, "channels": channels})     
        
        json_ret = {'id': 1, 'datas': datas}
        bluetooth_list = datas # blue tooth list
        dataqueue_test.put(json.dumps(json_ret))

    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("串口操作异常，请确认设备是否已连接,print_exception:")
        traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)
        localSerial.close()


def switch_blooth(imei, type, filter_para, socket_connect_sta, dataqueue, glQueue):
    global localSerial
    global receive_status
    global bleconnect_status
    closeDataReceive()
    closeLocalSerial()
    localSerial = openLocalSerial()
    #bleconnect_status = False
    #socket_connect_sta.ble_is_alive = False
    openBluetooth(imei, type, socket_connect_sta, glQueue, dataqueue, 8)
    error_ret_obj = DataSend(201, "success")
    if not bleconnect_status:
        error_ret_obj = DataSend(1010, "正在采集数据，暂无法关闭蓝牙设备！")
                    
    dataqueue.put(json.dumps(error_ret_obj, default=lambda obj: obj.__dict__, sort_keys=True))

def findBlooth(dataqueue_test, filter_para, socket_connect_sta, glQueue, phbFatherDefault):
    global bleconnect_status
    global bleconnect_dict
    global bluetooth_list
    try:

        bleconnect_dict["filter_para"] = filter_para

        if bleconnect_status == True:
            if not phbFatherDefault or bleconnect_dict["hardware_type"] == hardware_type_channel[phbFatherDefault]:
                openBluetooth(bleconnect_dict["imei"], bleconnect_dict["hardware_type"], socket_connect_sta, glQueue, dataqueue_test)
                time.sleep(3)
                json_ret = {'id': 1, 'datas': bluetooth_list}
                dataqueue_test.put(json.dumps(json_ret))
            else:
                bleconnect_status = False
                socket_connect_sta.ble_is_alive = False

                error_ret_obj = DataSend(1009, "硬件连接不匹配，请先断开原设备再连接新设备。")
                error_ret_str = json.dumps(error_ret_obj, default=lambda obj: obj.__dict__, sort_keys=True)
                dataqueue_test.put(error_ret_str)
        else:
            bleconnect_dict["phbFatherDefault"] = phbFatherDefault
            findHardware(dataqueue_test, phbFatherDefault)
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print("查找蓝牙设备异常,print_exception:")
        traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)

if __name__ == '__main__':
    openBluetooth("3CA551855EF6")

    openDataReceive()
    receive = threading.Thread(target=receiveData,args=(None))
    receive.setDaemon(True)
    receive.start()

    receive.join()
