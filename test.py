import asyncio
import json
import os
import random
import urllib
from datetime import datetime, date

import numpy as np
import pyedflib
from pyedflib import highlevel
import decimal



def signal_dictionary(channels_amount):
    signal = {
        'channels': [],
        'times': [],
    }
    signal['channels'] = [[] for _ in range(channels_amount)]
    return signal


def save_data2edf(edf_name, signals, start_date,max,min):
    """
    保存数据格式为edf
    """
    if signals.shape[0] == 1:
        channel_names = ['channel1']
    elif signals.shape[0] == 5:
        channel_names = ['channel1', 'channel2', 'channel3', 'channel4', 'channel5']
    elif signals.shape[0] == 8:
        channel_names = ['channel1', 'channel2', 'channel3', 'channel4', 'channel5', 'channel6', 'channel7', 'channel8']
    signal_headers = highlevel.make_signal_headers(channel_names, physical_max=max, physical_min=min,
                                                   sample_rate=8715, dimension='V')
    header = highlevel.make_header(patientname='X1', gender='F', startdate=start_date)
    print(signals.shape)
    highlevel.write_edf(edf_name, signals, signal_headers, header)
    # highlevel.write_edf_quick(edf_name, signals,250,digital=False)



if __name__ == "__main__":

    for i in range(8):
        # rand=random.randint(0,1)
        print(i)

    file_signal = signal_dictionary(8)
    file_op = open(r'D:\10-workspaces\naolu\psychic_health_desktop_serial_sdk\data\2021-03-31_19-56-55.txt')


    line = file_op.readline()
    while line:
        data_list = line.split(',')
        for i in range(8):
            for j in range(5):
                # print (">>",decimal.Decimal(data_list[i + (j * 5 + 1)]).quantize(decimal.Decimal('0.00')),float(data_list[i + (j * 5 + 1)]))
                file_signal['channels'][i].append(float(data_list[i + (j * 5 + 1)]))
                # file_signal['channels'][i].append(float(decimal.Decimal('1').quantize(decimal.Decimal('0.00'))))

        line = file_op.readline()
        # break
    print(np.array(file_signal['channels']))
    print("min:",np.array(file_signal['channels']).min())
    print("max:",np.array(file_signal['channels']).max())

    # # f = pyedflib.EdfWriter(r'D:\test.edf', 5, file_type=0)
    # # channel_names = ['channel1', 'channel2', 'channel3', 'channel4', 'channel5']
    # channel_names = ['channel1', 'channel2', 'channel3', 'channel4', 'channel5', 'channel6', 'channel7', 'channel8']
    # # signal_headers = highlevel.make_signal_headers(channel_names, physical_max=200, physical_min=-200,
    # #                                                sample_rate=250, dimension='uV')
    # # header = highlevel.make_header(patientname='X1', gender='F', startdate=start_date)
    #
    # signal_headers = highlevel.make_signal_headers(channel_names, physical_max=200000, physical_min=-200000,
    #                                                sample_rate=250, dimension='V')
    #
    #
    # header = highlevel.make_header(patientname='X1', gender='F', startdate=file_time)
    # print(file_signal['channels'])
    # highlevel.write_edf('test.edf', np.array(file_signal['channels']), signal_headers, header)

    file_time = datetime.strptime('2021-03-31_19-56-55', "%Y-%m-%d_%H-%M-%S")
    save_data2edf('test.edf', np.array(file_signal['channels']), file_time,np.array(file_signal['channels']).max(),np.array(file_signal['channels']).min())

    # f.setSignalHeaders(signal_headers)
    # f.setBirthdate(date(1951, 8, 2))
    # f.writeSamples(np.array(file_signal['channels'])[:])
    # f.close()
    signals, signal_headers, header = highlevel.read_edf(r'test.edf',None,None,False,True)
    print(np.array(signals).shape)
    print(signals)
    print(decimal.Decimal(signals[0][0]),decimal.Decimal(signals[0][1]),decimal.Decimal(signals[0][2]),decimal.Decimal(signals[0][3]))
    # write an edf file
    # signals = np.random.rand(5, 256 * 300) * 200  # 5 minutes of random signal
    # print(signals)
    # channel_names = ['ch1', 'ch2', 'ch3', 'ch4', 'ch5']
    # signal_headers = highlevel.make_signal_headers(channel_names, sample_rate=256)
    # header = highlevel.make_header(patientname='patient_x', gender='Female')
    # highlevel.write_edf(r'D:\zzy\test.edf', signals, signal_headers, header)
    # for i in range(1):
    #     print(i)
    # t=(int)(127/128)
    # print(t)
    # test=b'\xff\x1e\xff\x04\xde\xfe\xf4\x1b\xff!\x18\xff2\xcf\xfe\xfb&\xff\x7f\x8f\xff*\xeb\xfe\xee\xbb\xff\x9da\xff\x9b#\xff\xb2B\xff\xbf\xb1\xff\xa2\x8f\xff\xe8\x00\xff\xb1\xcf\xff\x95}\x00\xc9q\x00\xda\x0e\x00\xb8e\x00\xb0\n\x00\xd8\x9f\x00}\xa8\x00\xad\xc9\x00\xdb\x89\x00\xd5\xce\x00\xe2\x1d\x00\xb6\x98\x00\xa5\xe7\x00\xdb\x0f'
    # test_array=test.split(b'\xff\x1e\xff\x04\xde\xfe')
    # for i in range(len(test_array)):
    #     print(test_array[i])
    # bgn=test.find(b'\n\xff')
    # print(bgn)
    # yun_url = 'https://naolu-log.oss-cn-beijing.aliyuncs.com/whole_hat' + '/' + str(
    #     1) + '/' + os.path.basename('test.edf')
    # # 调用后台服务器提交url
    # file_size = str(os.path.getsize(r'D:\zzy\code\brain_hat\brain_hat\data\edf\2020-12-15_15-36-43.edf'))
    # request_data = {'featureUrl': yun_url, 'collectId': 1, 'fileSize': file_size}
    # ## headers中添加上content-type这个参数，指定为json格式
    # headers = {'Content-Type': 'application/json'}
    # ## post的时候，将data字典形式的参数用json包转换成json格式。
    # response = requests.post(url='http://192.168.0.120:9033/api/collect/saveUrl', headers=headers,
    #                          data=json.dumps(request_data))
    # a = np.array([[1, 2, 3, 4, 5, 6, 7, 8], [9, 10, 11, 12, 13, 14, 15, 16],[9, 12, 13, 12, 13, 14, 15, 16]])
    # test_str='0,2'
    # test_list=test_str.split(',')
    # test_list=list(map(int,test_list))
    # print(a[test_list])
    # file_url='https://naolu-log.oss-cn-beijing.aliyuncs.com/whole_hat/8/2020-12-04_14-06-15.edf'
    # urllib.request.urlretrieve(file_url, os.getcwd()+'\data'+'\edf1'+"\demo.edf")
    # file_name=file_url.split('/')[-1]
    # rootdir=os.getcwd() +'\data'+'\edf'
    # file_list=os.listdir(rootdir)
    #
    # for i in range(0,len(file_list)):
    #     print(file_list[i])
    #     if file_name==file_list[i]:
    #         print(file_name)
    # print(file_list)
    #
    # print(file_name)
    # signals, signal_headers, header = highlevel.read_edf(r'D:\zzy\test.edf')
    # print(signals.shape)
    # print(signals)
    # print(signal_headers)
    # print(header)
    # raw = read_raw_edf(r'D:\zzy\test.edf')
    # print(raw.info)
    # print(raw[:,:][0])
    # print(raw[:, :][0].shape)
    # print(raw[:, :][1].shape)
    # raw_list = raw[:, :][0].tolist()
    # file_signal = signal_dictionary(5)
    # file_op = open(r'D:\zzy\code\brain_hat\brain_hat\data\2020-12-22_11-38-41.txt')
    # line = file_op.readline()
    # while line:
    #     data_list = line.split(',')
    #     for i in range(5):
    #         for j in range(5):
    #             file_signal['channels'][i].append(float(data_list[i + (j * 5 + 1)]))
    #     line = file_op.readline()
    # print(np.array(file_signal['channels']).shape)
    # print(np.array(file_signal['channels'])[:,0:250])
    # starttime=datetime.strptime('2020-12-22_12-39-43', "%Y-%m-%d_%H-%M-%S")
    # save_data2edf('D:\\zzy\\test.edf', np.array(file_signal['channels'])[:,0:250], starttime)
    # signals, signal_headers, header = highlevel.read_edf(r'D:\zzy\test.edf')
    # print(signals.shape)
    # print(signals)

