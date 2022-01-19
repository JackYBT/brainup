import json
import random
import decimal

import sys,traceback

import binascii

import requests
import oss2

import process_signal
from rdb import update_attention_rets, update_emotion_rets, update_heart_beat_rets, update_blood_and_axis_rets
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


# 服务链接
SERVER_URL = "http://192.168.3.151:8084/broadcast/{}"


def dataAnalysis(socket_connect_sta, filter_para, type, dataqueue_test, glQueue,fbcca=None):
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
    wrong_size_count = 0
    t0 = datetime.now() 
    print("CHeckpoint 100")
    ###模型初始化###
    # fbcca = FBCCA()
    # time.sleep(1)
    ###############
    while True:
        try:
            #begin = datetime.now()  # 获得当前时间
            if socket_connect_sta.connect == False or socket_connect_sta.ble_is_alive == False or socket_connect_sta.command == 5:
                print('stop--analysis--thread--because--bleorsocket disccnect',dataqueue_test.qsize())
                break
            if not glQueue.empty():
                data = glQueue.get(block=False)

                samples = []
                
                str_insert = ''
                str_inserts=[]
                sample = []
                
                # 每次采集 5X5 数据，共循环5次
                # 组成 5X5X5 矩阵供算法端进行处理
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
         
                #total_count += 1
                #print("Length of samples", len(samples)) 
                for eeg_data in samples:

                    #print("Length of samples", len(samples))
                    # 每次小循环添加 1X8 数据
                    # 大循环构成 5X8 数据
                    for i in range(channel_mount):
                        wave_signal['channels'][i].append(eeg_data.channel_data[i])
                    samplenumber = samplenumber + 1
                    
                    # 每0.1秒执行下列代码
                    if samplenumber == 25:
                        samplenumber = 0
                        #wave_2 = []
                        wave_buffer = data_slither(wave_buffer, 25, np.array(wave_signal['channels']))
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
                            #TODO
                            temp = wave_2_1[:, (475 + 5 * i):(480 + 5 * i)]
                            draw_datas.append(np.round(temp, decimals=6))
                        draw_send = np.array(draw_datas)
                        draw_send = draw_send.transpose()
                        
                        # 将 5X8X5 reshape 成 8X25 
                        #draw_send_temp= np.swapaxes(draw_send,0,1).reshape((8,25))
                        # print("AFTER: ",draw_send_temp)
                        # print("-"*50) 
                        total_count += 1
                        #print("Total count: ", total_count)

                        #temp_cache.append(draw_send_temp)
                        # total_count = 20 代表第2秒时间，开始执行算法处理，此后每秒执行一次算法
                        # if total_count >= 20 and total_count % 10 == 0:
                        #     temp_cache = temp_cache[-20:]
                        #     #temp_cache 是最后2秒钟的数据，是20X（8X25)的矩阵:第一个5应该是 5个电极，第二个5应该是5个采样点
                        #     #需要对temp_cache进行预处理，并且放到模型里面算一下，然后把专注度的结果（0～100）存储到 result 里面。
                        #     #如果你用的是binary classification network，那你就吧最后的probability * 100 变成一个分数
                            
                        #     #t0 = datetime.now()

                        #     #Changing a 20X8X25 into a 8X500
                        #     temp_cache_reshape = np.swapaxes(temp_cache,0,1).reshape((8,500))
                            #temp_cache_reshape = np.zeros((500,8))

                            #for chan_i in range(8):
                            #    temp_cache_reshape[:,chan_i] = np.array(temp_cache)[:,chan_i,:].reshape(-1)
                            
                            # print("Temp_Cache_before", temp_cache)
                            # print("Temp_Cache_AFTER", temp_cache_reshape)
                            
                            # action_index,corr_max = fbcca.data_process(temp_cache_reshape)
                            # direction = ['up', 'down', 'left', 'right'][action_index]
                            # print("DIrection: ", direction)

                            # t1 = datetime.now()
                            # print("Model running time: ", t1-t0)
                            #print("CHECKPOINT 100")
                            #direction = random.choice(['up', 'down', 'left', 'right','jump', 'sprint','stop'])
                            #requests.get(SERVER_URL.format(direction)) 
                            #if fbcca.slicewindow():
                            #requests.get(SERVER_URL.format(direction))
                            
                            # TODO: Call Algo module
                            #action_index, corr_max = fbcca.data_process(temp_cache_reshape)
                            #direction = ['up', 'down', 'left', 'right'][action_index]

                            #direction = random.choice(['up', 'down', 'left', 'right','jump', 'sprint','stop'])
                            #requests.get(SERVER_URL.format(direction))
                        
                        # draw_send = DataSend(3, draw_send)
                        # draw_send_str = json.dumps(draw_send, default=lambda obj: obj.__dict__, sort_keys=True)

                        # if filter_para.start_record: 
                        #     dataqueue_test.put(draw_send_str)                            
                        #     #Send data to MySQL database
                        #     #print(">")
                        # elif type in (1, 2):     #1通道和5通道继续按现有方式输出信号
                        #     send_func(2, get_random_list(channel_mount),dataqueue_test)

                        #wave_signal = signal_dictionary(channel_mount)
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

def send_func(id, data, dataqueue_test):
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
