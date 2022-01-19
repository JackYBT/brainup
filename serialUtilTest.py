
import serial #导入模块
import time
import threading
import configure
import binascii

from datetime import datetime

#端口，GNU / Linux上的/ dev / ttyUSB0 等 或 Windows上的 COM3 等
#com_name="COM3"
#波特率，标准值之一：50,75,110,134,150,200,300,600,1200,1800,2400,4800,9600,19200,38400,57600,115200
#bit_rate=115200
#超时设置,None：永远等待操作，0为立即返回请求结果，其他值为等待超时时间(单位为秒）
from converterGen3 import gen3SamplesGenerate

timex=5

def openLocalSerial():
    config= configure.getConfig()
    ser = serial.Serial(config['com_name'], config['bit_rate'], timeout=timex)
    ser.write("AT\r\n".encode("gbk"))
    ret = ser.readall()
    if len(ret) < 2:
        print("无法打开串口端口，请稍后重试")
    else:
        # ret = retHex.decode("gbk")
        print("串口连接状态：", ret.decode("gbk"))
        if ret.decode("gbk").find("OK") > -1:
            if ser.is_open:
                ser.write("AT+BAUD8\r\n".encode("gbk"))
                time.sleep(0.2)
                ser.write("AT+HOSTEN1\r\n".encode("gbk"))
                time.sleep(0.2)
                print(ser.readall().decode("gbk"))
            else:
                print("串口未打开")
        else:
            print("串口打开异常")

    return ser

def closeLocalSerial():
    global localSerial
    if localSerial.is_open:
        localSerial.close();
        print("关闭串口：串口已关闭")
    else:
        print("关闭串口：已是关闭状态")


localSerial = openLocalSerial()

def closeDataReceive():
    global localSerial
    if localSerial.is_open:
        s1 = 'AHB+START=0'
        s2 = 'AHB+MODE=1'   #数据传输模式  0自校准模式,1阻抗模式,2正常测试模式
        #localSerial.write(s1.encode("utf-8"))
        time.sleep(0.1)
        localSerial.write(s2.encode("utf-8"))
        time.sleep(0.1)
        print("关闭数据传输：已关闭串口蓝牙数据传输")
    else:
        print("关闭数据传输：串口未打开")

def openDataReceive():
    global localSerial
    if not localSerial.is_open:
        localSerial = openLocalSerial()
        #TODO: 添加自动连接蓝牙设备

    if localSerial.is_open:
        s1 = 'AHB+MODE=3'
        s2 = 'AHB+START=1'  # 数据传输模式  0自校准模式,1阻抗模式,2正常测试模式,3校准模式（不需要关注）
        localSerial.write(s1.encode("utf-8"))
        time.sleep(0.1)
        localSerial.write(s2.encode("utf-8"))
        time.sleep(0.1)
        print("打开数据传输：已打开串口蓝牙数据传输")

def openBluetooth(imei):
    global localSerial
    if localSerial.is_open:
        s1 = "AT+CONN"+imei+"\r\n"
        localSerial.write(s1.encode("gbk"))
        #localSerial.write("AT+CONN3CA551855EF6\r\n".encode("gbk"))
        ret = localSerial.readall().decode("gbk").split('+')
        print(">>AT+CONN:", ret)
        for msg in ret:
            if msg.find("OK") < 0:
                if msg.find(imei) >= 0:
                    print("串口连接蓝牙:已连接")
                    break;
                else:
                    print("串口连接蓝牙：连接异常，请重试", msg)



def closeBluetooth():
    global localSerial
    #目前串口连接的蓝牙设备不支持单独关闭



def receiveData():
    global localSerial
    if localSerial.is_open:
        unpacking_record = b''
        while True:
            print(">>",localSerial.read(130).hex())
            # n = localSerial.in_waiting
            # if n > 0:
            #     data = localSerial.read(n)
            #     #print(">>>>>>", binascii.hexlify(data))
            #     #print(">>>>>>", binascii.hexlify(data))
            #     unpacking_record = unpacking_record + data
            #
            # if len(unpacking_record) >= 130:
            #     array_data = unpacking_record.split(b'##>')
            #     for i in range(len(array_data) - 1):
            #         print(">>>>",array_data[i])
            #         # data_satellite, str_insert, sample = gen3SamplesGenerate(array_data[i])
            #         # file.write(datetime.now().strftime('%H-%M-%S.%f') + ',' + str_insert + '\n')
            #     unpacking_record = array_data[len(array_data) - 1]




def findHardware():
    global localSerial
    try:
        if not localSerial.is_open:
            print("串口已关闭，准备重新打开")
            localSerial = openLocalSerial()
        else:
            print("串口已打开")

        devices = []
        result = localSerial.write("AT+SCAN\r\n".encode("gbk"))
        time.sleep(0.2)
        deviceInfo = localSerial.readall()

        print("查询设备信息:",deviceInfo)
        deviceName = str(deviceInfo.replace(b'\r\n',b''), encoding="utf-8").split('+')
        for nm in deviceName:
            if nm.find('Brain')>0 or nm.find('BRAIN') >0:
                print("Brain Device Info:",nm)
                device = nm[6:].split(',')
                print(">>" ,device[2] + ';' + device[0])
                devices.append(device[2] + ';' + device[0])

        return list(set(devices))
    except Exception as e:
        print("串口操作异常，请确认设备是否已连接")
        print(e)


if __name__ == '__main__':
    #localSerial.close()
    #findHardware()
    openBluetooth("3CA551855EF6")

    openDataReceive()
    receive = threading.Thread(target=receiveData)
    receive.setDaemon(True)
    receive.start()

    receive.join()

    time.sleep(10)
    closeDataReceive()
    time.sleep(30)
    openDataReceive()
    time.sleep(10)
