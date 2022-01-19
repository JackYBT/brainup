import json
import random
import decimal

import sys,traceback

import binascii

import requests
import oss2

import process_signal
import rdb
import configure
from converter import DataProcessor, DataSatellite
from converterGen1 import gen1SamplesGenerate
from converterGen2 import gen2SamplesGenerate
from converterGen3 import gen3SamplesGenerate
from data_processing import data_slither
from data_transfer import DataSend
import time
import numpy as np
import os
from datetime import datetime

from model_fbcca import FBCCA

SERVER_URL = "http://127.0.0.1:8084/broadcast/{}"
fbcca = FBCCA()
ten_second_window = []

# filter_param = 1
from edf_file_analysis import data_freqs_sorted, data_amplitude
from file_analysis import save_data2edf

#0:红色 1:绿色 2:白色 3:蓝色
impedance_color = {"red":0,"green":1,"white":2,"blue":3}

def signal_dictionary(channels_amount):
    signal = {
        'channels': [],
        'times': [],
    }
    signal['channels'] = [[] for _ in range(channels_amount)]
    return signal

def __type_to_chan_freq__(type):
    channel_mount = 4
    FREQUENCY = 200
    if type == 1:
        channel_mount = 1
        FREQUENCY = 250
    elif type == 2:
        channel_mount = 5
        FREQUENCY = 250
    elif type==3:
        channel_mount=8
        FREQUENCY = 250
    else:
        channel_mount = 4
        FREQUENCY = 200
    return channel_mount, FREQUENCY


#SERVER_URL = "http://192.168.3.151:8084/broadcast/{}"

def dataAnalysis(socket_connect_sta, filter_para, type, dataqueue_test, glQueue):
    config = configure.getConfig()
    impedance_sever = int(config['impedance_sever'])    #阻抗未连接阈值
    impedance_diff = int(config['impedance_diff'])      #阻抗连接最大值和最小值的差值

    impedance_point = []
    impedance_data  = []

    processor = DataProcessor()
    samplenumber = 0
    channel_mount, FREQUENCY = __type_to_chan_freq__(type)

    wave_buffer = np.zeros([channel_mount, FREQUENCY * 2])
    wave_signal = signal_dictionary(channel_mount)
    imp_data_signal = signal_dictionary(channel_mount)
    # save_signal = signal_dictionary(10)
    unpacking_record = b''
    satellite = None
    imp_count = 0
    # draw_datas = []
    # draw_num = 0
    # str_insert=''

    total_count = 0
    temp_cache = []
    while True:
        try:
            begin = datetime.now()  # 获得当前时间
            if socket_connect_sta.connect == False or socket_connect_sta.ble_is_alive == False or socket_connect_sta.command == 5:
                print('stop--analysis--thread--because--bleorsocket disccnect',dataqueue_test.qsize())
                break
            if not glQueue.empty():
                data = glQueue.get(block=False)
                if len(data) == 3 and type == 2:
                    print(binascii.b2a_hex(data))
                    battery = chr(int(data[1]))
                    battery_data = DataSend(11, str(battery))
                    battery_str = json.dumps(battery_data, default=lambda obj: obj.__dict__, sort_keys=True)
                    dataqueue_test.put(battery_str)
                    # dataqueue.put(zk_str)
                samples = []
                str_insert = ''
                str_inserts=[]
                sample = []
                if type == 1 :
                    unpacking_record = unpacking_record + data
                    if len(unpacking_record) >= 85:
                        array_data = unpacking_record.split(b'\x0a\xff')
                        for i in range(len(array_data) - 1):
                            data_satellite, str_insert, sample = gen1SamplesGenerate(array_data[i])
                            if data_satellite != None and data_satellite.data_type == 3:
                                str_inserts.append(str_insert)
                                for sample_tmp in sample:
                                    samples.append(sample_tmp)
                        unpacking_record = array_data[len(array_data) - 1]
                if type == 2 :
                    unpacking_record = unpacking_record + data
                    if len(unpacking_record) >= 85:
                        array_data = unpacking_record.split(b'\x0a\xff')
                        for i in range(len(array_data) - 1):
                            data_satellite, str_insert, sample = gen2SamplesGenerate(array_data[i])
                            if data_satellite != None and data_satellite.data_type == 3:
                                str_inserts.append(str_insert)
                                for sample_tmp in sample:
                                    samples.append(sample_tmp)
                        unpacking_record = array_data[len(array_data) - 1]

                if type == 3:
                    unpacking_record = unpacking_record + data
                    if len(unpacking_record) >= 130:
                        # print("unpacking_record:" ,unpacking_record)
                        array_data = unpacking_record.split(b'##>')
                        for i in range(len(array_data) - 1):
                            if len(array_data[i]) > 0:
                                data_satellite, str_insert, sample = gen3SamplesGenerate(array_data[i])
                                if data_satellite != None:
                                    if data_satellite.data_type == 3:
                                        str_inserts.append(str_insert)
                                        for sample_tmp in sample:
                                            samples.append(sample_tmp)

                        unpacking_record = array_data[len(array_data) - 1]

                if len(sample) > 0 and data_satellite != None:
                    satellite = DataSatellite()
                    satellite.data_type = data_satellite.data_type
                    satellite.electric_state = data_satellite.electric_state
                    satellite.electric_charge = data_satellite.electric_charge
                    if data_satellite.data_type == 2:
                        if filter_para.start_record:
                            filter_para.imp_save_file.close()

                            if filter_para.write_eeg_header == True:
                                filter_para.save_file.write('%Number of channels = 8\n')
                                filter_para.save_file.write('%Sample Rate = 250 Hz\n')
                                filter_para.save_file.write('%阻抗最后一秒 = ' + str(impedance_data)[1:-1] + '\n')
                                filter_para.save_file.write('%阻抗未过通道 = ' + str(np.where(np.array(impedance_point) != impedance_color["green"])[0]+1)[1:-1] + '\n')
                                filter_para.write_eeg_header = False


                        if hasattr(data_satellite,'imp_data'):
                            satellite.imp_data = data_satellite.imp_data
                        if not filter_para.start_record:
                            imp_insert_real=datetime.now().strftime('%H-%M-%S.%f') + ',' +str_insert
                            filter_para.imp_save_file.flush()
                            filter_para.imp_save_file.write(imp_insert_real+'\n')

                if filter_para.satellite_status:
                    if satellite!=None:
                        fullbattery_hour = {1:8,5:8,8:10}
                        remaining_time=(int)(satellite.electric_charge*fullbattery_hour[channel_mount]*60/100)
                        send_msg = [satellite.electric_state, satellite.electric_charge,
                                    remaining_time]
                        send_func(10, send_msg, dataqueue_test)
                        filter_para.satellite_status = False

                if type == 3:
                    if not filter_para.start_record:

                        if satellite != None:
                            imp_count=imp_count+1
                            # print("size:", glQueue.qsize())
                            # print("imp count:" + str(imp_count) + ": ",data_satellite.imp_data)
                            for i in range(channel_mount):
                                if hasattr(data_satellite,'imp_data'):
                                    imp_data_signal['channels'][i].append(data_satellite.imp_data[i])
                            if imp_count>=50:
                                fft_data = abs(np.fft.rfft(imp_data_signal['channels']) / imp_count)
                                fft_max=np.amax(fft_data,axis=1)
                                print("impedance:",fft_max)
                                
                                imp_count = 0
                                imp_data_signal = signal_dictionary(channel_mount)

                                impedance_point = [-1,-1,-1,-1,-1,-1,-1,-1]
                                diff_max = -1
                                diff_max_value = -999999
                                diff_min = -1
                                diff_min_value = 999999
                                impedance_data = fft_max.tolist()
                                for j in range(channel_mount):
                                    if impedance_data[j] > impedance_sever:    #大于设定的未连接阻抗显示为白
                                        impedance_point[j] = impedance_color["white"]
                                    else:
                                        if impedance_data[j] > diff_max_value and impedance_data[j] <= impedance_sever : #获取最大值
                                            diff_max_value = impedance_data[j]
                                            diff_max = j
                                        if impedance_data[j] < diff_min_value and impedance_data[j] <= impedance_sever : #获取最小值
                                            diff_min_value = impedance_data[j]
                                            diff_min = j

                                for j in range(channel_mount):
                                    if impedance_color["white"] != impedance_point[j]:       #先将小于阻抗阻断设定值的全部点标为绿色
                                        impedance_point[j] = impedance_color["green"]
                                if diff_max >= 0 and diff_min >= 0 and abs(diff_max_value - diff_min_value) > impedance_diff:    #如果最大最小差值大于设定就标红蓝点
                                    impedance_point[diff_max] = impedance_color["red"]
                                    impedance_point[diff_min] = impedance_color["blue"]

                                # print("impedance_point:" ,impedance_point)
                                send_func(2,impedance_point,dataqueue_test)

                                if filter_para.test_start_record == True:
                                    if len(np.where(np.array(impedance_point)==impedance_color["green"])[0]) == 8 or ( len(np.where(np.array(impedance_point)==impedance_color["white"])[0]) == 2
                                             and len(np.where(np.array(impedance_point)==impedance_color["green"])[0]) == 6 ):
                                        error_ret_obj = DataSend(1012, "success")
                                        error_ret_str = json.dumps(error_ret_obj, default=lambda obj: obj.__dict__, sort_keys=True)
                                        dataqueue_test.put(error_ret_str)
                                        filter_para.test_start_record = False
                                    else:
                                        error_ret_obj = DataSend(1011, "阻抗调试不合格，确认开始或取消继续调试")
                                        error_ret_str = json.dumps(error_ret_obj, default=lambda obj: obj.__dict__, sort_keys=True)
                                        dataqueue_test.put(error_ret_str)
                                        filter_para.test_start_record = False

                if filter_para.save_action:
                    hardWareType = 'hardWareType' + str(type)
                    socket_connect_sta.command = 5
                    if filter_para.start_record == True:
                        filter_para.save_file.flush()
                        filter_para.save_file.close()
                        file_operate(filter_para)
                    file_suc = DataSend(6, 'success')
                    file_suc_str = json.dumps(file_suc, default=lambda obj: obj.__dict__, sort_keys=True)
                    dataqueue_test.put(file_suc_str)

                elif filter_para.start_record and len(str_inserts) != 0:
                    for str_insert_tmp in str_inserts:
                        str_insert_real=datetime.now().strftime('%H-%M-%S.%f') + ',' +str_insert_tmp
                        filter_para.save_file.write(str_insert_real + '\n')
                    # str_insert = datetime.now().strftime('%H-%M-%S.%f') + ',' + str_insert
                    # filter_para.save_file.write(str_insert + '\n')

                for eeg_data in samples:
                    # value=sum(eeg_data.channel_data[:4])
                    # wave_buffer = shift(wave_buffer, -1, cval=value)

                    for i in range(channel_mount):
                        wave_signal['channels'][i].append(eeg_data.channel_data[i])

                    samplenumber = samplenumber + 1

                    ten_second_window_raw = []

                    if samplenumber == 25:
                        samplenumber = 0
                        wave_2 = []



                        wave_buffer = data_slither(wave_buffer, 25, np.array(wave_signal['channels']))
                        #print("Filter_Para.notch_filter", filter_para.notch_filter)
                        if filter_para.notch_filter == 2:
                            wave_2_0 = wave_buffer
                        elif filter_para.notch_filter == 1:
                            wave_2_0 = process_signal.butter_bandstop_filter(wave_buffer, 49, 51, FREQUENCY, 4)
                        elif filter_para.notch_filter == 3:

                            wave_2_0 = process_signal.butter_bandstop_filter(wave_buffer, 59, 61, FREQUENCY)
                        if filter_para.filter_param == 1:

                            wave_2_1 = wave_2_0
                        elif filter_para.filter_param == 2:

                            wave_2_1 = process_signal.butter_bandpass_filter(wave_2_0, 0.35, 35, FREQUENCY, 4)
                            # wave_2 = np.around(wave_2_1[:, -1], decimals=3).tolist()
                        elif filter_para.filter_param == 3:

                            wave_2_1 = process_signal.butter_bandpass_filter(wave_2_0, 1, 50, FREQUENCY, 4)
                            # wave_2 = np.around(wave_2_1[:, -1], decimals=3).tolist()
                        elif filter_para.filter_param == 4:

                            wave_2_1 = process_signal.butter_bandpass_filter(wave_2_0, 7, 13, FREQUENCY, 4)
                            # wave_2_2 = process_signal.butter_bandstop_filter(wave_2_1, 13, 30, FREQUENCY)
                            # wave_2 = np.around(wave_2_2[:, -1], decimals=3).tolist()
                        elif filter_para.filter_param == 5:

                            wave_2_1 = process_signal.butter_bandpass_filter(wave_2_0, 15, 50, FREQUENCY, 4)
                        elif filter_para.filter_param == 6:

                            wave_2_1 = process_signal.butter_bandpass_filter(wave_2_0, 5, 50, FREQUENCY, 4)
                        draw_datas = []
                        for i in range(5):
                            temp = wave_2_1[:, (475 + 5 * i):(480 + 5 * i)]
                            draw_datas.append(np.round(temp, decimals=2))
                        draw_send = np.array(draw_datas) 
                        #*****SEPARATE STUFF 
                        draw_send_temp = draw_send.transpose()
                        # 将 5X8X5 reshape 成 8X25 
                        draw_send_temp= np.swapaxes(draw_send_temp,0,1).reshape((8,25))
                        total_count += 1
                        
                        temp_cache.append(draw_send_temp)
                        #total_count = 20 代表第2秒时间，开始执行算法处理，此后每秒执行一次算法
                        if total_count >= 20 and total_count % 10 == 0:
                            temp_cache = temp_cache[-20:]
                            #Changing a 20X8X25 into a 500X8
                            temp_cache_reshape = np.swapaxes(temp_cache,0,1).reshape((8,500)).transpose()
                            #temp_cache_reshape = np.swapaxes(temp_cache,0,1).reshape((8,500))

                            ten_second_window.append(temp_cache_reshape)
                            
                            # if total_count == 100:
                            #     np.save("temp_cache_10_Second_15hz_cong.npy", ten_second_window)
                            #     break
                            #print("Temp_cache_reshape[:10] & shape", temp_cache_reshape[:10], temp_cache_reshape.shape)
                            action_index,corr_max = fbcca.data_process(temp_cache_reshape)
                            #requests.get(SERVER_URL.format('left'))

                            requests.get(SERVER_URL.format('left'))
                            if fbcca.slicewindow():
                                direction = ['up', 'down', 'left', 'right','action'][action_index]
                                print("Direction: ", direction)
                                requests.get(SERVER_URL.format(direction))
                                
                            else:
                                print("Direction as previous direction")

                            #requests.get(SERVER_URL.format(direction))

                        
                        #***SEPARATE STUFF ENDS
                        draw_send = draw_send.transpose().tolist()
                        draw_send = DataSend(3, draw_send)
                        draw_send_str = json.dumps(draw_send, default=lambda obj: obj.__dict__, sort_keys=True)
                        if filter_para.start_record:
                            dataqueue_test.put(draw_send_str)
                            #print(">")
                        elif type in (1, 2):     #1通道和5通道继续按现有方式输出信号
                            send_func(2, get_random_list(channel_mount),dataqueue_test)

                        wave_signal = signal_dictionary(channel_mount)
            #time.sleep(0.01)
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print("数据分析处理异常, print_exception:")
            traceback.print_exception(exc_type, exc_value, exc_traceback,limit=2, file=sys.stdout)

def get_random_list(channel_mount):
    ret_list=[]
    for i in range(channel_mount):
        #ret=random.randint(0,1)
        ret_list.append(1)
    return ret_list
def file_operate(filter_para):
    if filter_para.hardware_type==3:
        channel_amount=8
    elif filter_para.hardware_type==2:
        channel_amount=5
    elif filter_para.hardware_type==1:
        channel_amount=1
    file_signal = signal_dictionary(channel_amount)

    file_name = os.path.splitext(os.path.basename(filter_para.save_file_path + '.txt'))[0]
    file_name_array = file_name.split('_')
    file_time = datetime.strptime(file_name_array[4] + '_' + file_name_array[5], "%Y-%m-%d_%H-%M-%S")

    file_op = open(filter_para.save_file_path + '.txt')
    line = file_op.readline()
    while line:
        if not line.startswith('%'):
            data_list = line.split(',')
            for i in range(channel_amount):
                for j in range(5):
                    file_signal['channels'][i].append(float(data_list[i + (j * channel_amount + 1)]))
        line = file_op.readline()
    file_op.close()
    # edf_file_path=filter_para.save_file_path+'.edf'
    # is_exists = os.path.exists(filter_para.file_path + '/edf')
    # if not is_exists:
    #     os.makedirs(filter_para.file_path + '/edf')
    edf_tmp_file = './' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.edf'
    src_edf_file_path = edf_tmp_file
    file_name_new = file_name.replace(filter_para.user_mode, configure.mode[filter_para.user_mode])
    edf_file_path = filter_para.edf_file_path  + '/' + file_name_new + '.edf'
    # print(">>edf:", np.array(file_signal['channels']))
    print(src_edf_file_path, edf_file_path)
    save_data2edf(src_edf_file_path, np.array(file_signal['channels']), file_time)
    edf_file_rename(src_edf_file_path, edf_file_path)
    auth = oss2.Auth('LTAI4G1LwPb2i4Cp5d3A3wUq', 'qe0FiUtWwiYSsSdTAHlYkPMvMiHXuS')
    bucket = oss2.Bucket(auth, 'https://oss-cn-beijing.aliyuncs.com', 'south-china-university-of-technology')
    object_name = 'whole_hat' + '/' + str(filter_para.save_id) + '/' + os.path.basename(edf_file_path)
    bucket.put_object_from_file(object_name, edf_file_path)
    yun_url = 'https://south-china-university-of-technology.oss-cn-beijing.aliyuncs.com/whole_hat' + '/' + str(
        filter_para.save_id) + '/' + os.path.basename(edf_file_path)
    # 调用后台服务器提交url
    file_size = str(os.path.getsize(edf_file_path))
    request_data = {'featureUrl': yun_url, 'collectId': filter_para.save_id, 'fileSize': file_size,'userNumber':filter_para.user_name}
    ## headers中添加上content-type这个参数，指定为json格式
    headers = {'Content-Type': 'application/json'}
    ## post的时候，将data字典形式的参数用json包转换成json格式。
    # response = requests.post(url='http://101.200.216.197:9033/api/collect/saveUrl', headers=headers,
    #                          data=json.dumps(request_data))
    config = configure.getConfig()
    response = requests.post(url=config['api_server']+'/api/collect/saveUrl', headers=headers,
                             data=json.dumps(request_data))

    file_rename(filter_para)

def send_func(id, data,dataqueue_test):
    send_data = DataSend(id, data)
    send_data_str = json.dumps(send_data, default=lambda obj: obj.__dict__, sort_keys=True)
    dataqueue_test.put(send_data_str)

def edf_file_rename(src_name, to_name):
    os.rename(src_name, to_name)

def file_rename(filter_para):
    file_name = filter_para.file_name
    file_name_new = file_name.replace(filter_para.user_mode,configure.mode[filter_para.user_mode])
    os.rename(filter_para.file_path + '/' + file_name + '_imp.txt',filter_para.file_path + '/' + file_name_new + '_imp.txt')
    os.rename(filter_para.file_path + '/' + file_name + '_'+ str(filter_para.save_id) +'.txt',filter_para.file_path + '/' + file_name_new + '_' + str(filter_para.save_id) + '.txt')
