import json
import os
import sys
import urllib
import zipfile
from datetime import datetime

import numpy as np
from mne.io import read_raw_edf
from pyedflib import highlevel

import process_signal
from data_transfer import DataSend

file_dictory = {}


def file_filter(file_url, notch_filter, filter_param, page_size, page_number, vertical_size):
    # file_name=file_url.split('/')[-1]
    # if file_name in file_dictory:
    #     whole_raw=file_dictory.get(file_name)
    #     raw_list=whole_raw[0:5].tolist()
    #     time_list=whole_raw[5].tolist()
    #     data_file = DataSend(7, raw_list)
    #     data_file.times = time_list
    #
    #     data_file_json = json.dumps(data_file, default=lambda obj: obj.__dict__, sort_keys=True)
    #     # dataqueue.put(data_file_json)
    #     return data_file_json
    # file_path = file_get_path(file_url)
    # raw = read_raw_edf(file_path)
    # # file_dictory[file_name] = raw
    # # data_file_json=get_file_ret_data(raw)
    # print(raw.info)
    # # print(raw[:, :][0].shape)
    # # print(raw[:, :][1].shape)
    # # raw_round=np.round(raw[:, :][0],decimals=6)
    # raw_round = raw[:, :][0]
    # times=raw[:, :][1]
    # whole_raw=np.vstack((raw_round,times))
    # file_dictory[file_name]=whole_raw
    whole_raw = get_file_data(file_url)
    total_page = np.math.ceil(whole_raw.shape[1] / (page_size * 250))

    if page_number <= total_page:
        if page_number>1:
            start_filter_index=(page_number-2)*page_size*250
        else:
            start_filter_index=(page_number - 1) * page_size * 250
        start_index = (page_number - 1) * page_size * 250
        end_index = (page_number) * page_size * 250
    else:
        if page_number>1:
            start_filter_index=(page_number-2)*page_size*250
        else:
            start_filter_index=(page_number - 1) * page_size * 250
        start_index = (total_page - 1) * page_size * 250
        end_index = total_page * page_size * 250
    # ret_raw=whole_raw[0:5,start_index:end_index].copy()
    ret_raw = whole_raw[0:(whole_raw.shape[0] - 1), start_filter_index:end_index].copy()

    time_raw = whole_raw[-1][start_index:end_index]
    raw_filter = data_filter(ret_raw, notch_filter, filter_param)
    if page_number>1:
        raw_filter=raw_filter[:,page_size * 250:]
    raw_filter_last=raw_filter[:,-1]
    raw_filter=np.column_stack((raw_filter,raw_filter_last))
    original_data = np.round(raw_filter.copy(),decimals=6)
    for i in range(raw_filter.shape[0]):
        if vertical_size == 1:
            raw_filter[i] = (raw_filter[i]) * 1 + 100 * (2 * (raw_filter.shape[0]-1-i) + 1)
        elif vertical_size == 2:
            raw_filter[i] = (raw_filter[i]) * 1 + 50 * (2 * (raw_filter.shape[0]-1-i) + 1)
        elif vertical_size == 3:
            raw_filter[i] = (raw_filter[i]) * 1 + 10 * (2 * (raw_filter.shape[0]-1-i) + 1)
        elif vertical_size == 4:
            raw_filter[i] = (raw_filter[i]) * 1 + 5 * (2 * (raw_filter.shape[0]-1-i) + 1)
        # if vertical_size == 1:
        #     raw_filter[i] = (raw_filter[i]) * 1 + 0.04 * (2 - i)
        # elif vertical_size == 2:
        #     raw_filter[i] = (raw_filter[i]) * 2 + 0.04 * (2 - i)
        # elif vertical_size == 3:
        #     raw_filter[i] = (raw_filter[i]) * 3 + 0.04 * (2 - i)
        # elif vertical_size == 4:
        #     raw_filter[i] = (raw_filter[i]) * 5 + 0.04 * (2 - i)

    # raw_list = raw_round.tolist()
    channel_number = raw_filter.shape[0]
    raw_list = np.round(raw_filter, decimals=6)
    if channel_number==1:
        raw_list[[0],:]=raw_list[[0],:]
        original_data[[0],:]=original_data[[0],:]
    elif channel_number==5:
        raw_list[[0,1,2,3,4],:]=raw_list[[4,3,2,1,0],:]
        original_data[[0,1,2,3,4],:]=original_data[[4,3,2,1,0],:]
    elif channel_number==8:
        raw_list[[0, 1, 2, 3, 4,5,6,7], :] = raw_list[[7,6,5,4, 3, 2, 1, 0], :]
        original_data[[0, 1, 2, 3, 4,5,6,7], :] = original_data[[7,6,5,4, 3, 2, 1, 0], :]

    raw_list = raw_list.tolist()
    raw_list.reverse()
    original_data = original_data.tolist()
    original_data.reverse()
    # last_raw_list=raw_list[:,-1]
    # raw_list=np.column_stack((raw_list,last_raw_list)).tolist()
    #raw_list.append(raw_list[len(raw_list)-1])
    # raw_list = raw_filter.tolist()
    time_list = time_raw.tolist()
    time_list.append(time_list[len(time_list)-1]+0.004)
    # raw_list=raw_list.tolist()
    # time_list = times.tolist()
    data_file = DataSend(7, raw_list)
    data_file.times = time_list
    data_file.page_number = page_number
    data_file.page_size = page_size
    data_file.total_page = total_page
    data_file.original_data=original_data
    data_file.channel_number=raw_filter.shape[0]
    data_file_json = json.dumps(data_file, default=lambda obj: obj.__dict__, sort_keys=True)
    # file_dictory['2020-12-07_10-13-11']=data_file_json
    # print(sys.getsizeof(data_file_json))
    # dataqueue.put(data_file_json)
    # print(data_file_json)
    return data_file_json



def get_file_ret_data(raw):
    raw_list = raw[:, :][0].tolist()
    # raw_list=raw_list.tolist()
    time_list = raw[:, :][1].tolist()
    data_file = DataSend(7, raw_list)
    data_file.times = time_list

    data_file_json = json.dumps(data_file, default=lambda obj: obj.__dict__, sort_keys=True)
    return data_file_json


def data_dump(start_time, notch_filter, filter_param, file_url, channels, vertical_size):
    start_index = start_time * 250
    end_index = (start_time + 5) * 250
    whole_raw = get_file_data(file_url)
    channel_list = channels.split(',')
    channel_list = list(map(int, channel_list))
    # dump_data=whole_raw[channel_list][:,start_index:end_index].copy()
    dump_data = whole_raw[0:(whole_raw.shape[0] - 1):, start_index:end_index].copy()

    dump_data = data_filter(dump_data, notch_filter, filter_param)
    dump_data_last=dump_data[:,-1]
    dump_data=np.column_stack((dump_data,dump_data_last))
    for i in range(dump_data.shape[0]):
        # if vertical_size == 1:
        #     dump_data[i] = (dump_data[i]) * 1 + 0.04 * (2 - i)
        # elif vertical_size == 2:
        #     dump_data[i] = (dump_data[i]) * 2 + 0.04 * (2 - i)
        # elif vertical_size == 3:
        #     dump_data[i] = (dump_data[i]) * 3 + 0.04 * (2 - i)
        # elif vertical_size == 4:
        #     dump_data[i] = (dump_data[i]) * 5 + 0.04 * (2 - i)
        if vertical_size == 1:
            dump_data[i] = (dump_data[i]) * 1 + 100 * (2 * (dump_data.shape[0]-1-i) + 1)
        elif vertical_size == 2:
            dump_data[i] = (dump_data[i]) * 1 + 50 * (2 * (dump_data.shape[0]-1-i) + 1)
        elif vertical_size == 3:
            dump_data[i] = (dump_data[i]) * 1 + 10 * (2 * (dump_data.shape[0]-1-i) + 1)
        elif vertical_size == 4:
            dump_data[i] = dump_data[i] * 1 + 5 * (2 * (dump_data.shape[0]-1-i) + 1)

    time_list = whole_raw[-1][start_index:end_index].tolist()
    time_list.append(time_list[len(time_list) - 1] + 0.004)
    dump_obj = DataSend(8, dump_data.tolist())
    dump_obj.times = time_list
    dump_obj.channel_number=dump_data.shape[0]
    dump_obj.dump_channels = channel_list
    dump_json = json.dumps(dump_obj, default=lambda obj: obj.__dict__, sort_keys=True)
    return dump_json

    # data_raw=


def get_file_data(file_url):
    file_name = file_url.split('/')[-1]
    if file_name in file_dictory:
        whole_raw = file_dictory.get(file_name)
        return whole_raw

    file_path = file_get_path(file_url)
    raw = read_raw_edf(file_path)
    # file_dictory[file_name] = raw
    # data_file_json=get_file_ret_data(raw)
    print(raw.info)
    # print(raw[:, :][0].shape)
    # print(raw[:, :][1].shape)
    # raw_round=np.round(raw[:, :][0],decimals=6)
    raw_round = raw[:, :][0]
    times = raw[:, :][1]
    whole_raw = np.vstack((raw_round, times))
    file_dictory[file_name] = whole_raw
    return whole_raw


def file_get_path(file_url):
    file_name = file_url.split('/')[-1]
    rootdir = os.getcwd() + '/edf/' + file_name.split("_")[2] + '/' + file_name.split("_")[0]
    file_list = os.listdir(rootdir)
    for i in range(0, len(file_list)):
        if file_name == file_list[i]:
            return rootdir + '/' + file_name
    urllib.request.urlretrieve(file_url, rootdir + '/' + file_name)
    return rootdir + '/' + file_name


def data_filter(data, notch_filter, filter_param):
    frequency = 250
    if notch_filter == 2:
        data_notch = data
    elif notch_filter == 1:
        data_notch = process_signal.butter_bandstop_filter(data, 49, 51, frequency, 4)
    elif notch_filter == 3:
        data_notch = process_signal.butter_bandstop_filter(data, 59, 61, frequency, 4)

    if filter_param == 1:
        data_filter = data_notch
    elif filter_param == 2:
        data_filter = process_signal.butter_bandpass_filter(data_notch, 0.35, 35, frequency, 4)
    elif filter_param == 3:
        data_filter = process_signal.butter_bandpass_filter(data_notch, 1, 50, frequency, 4)
    elif filter_param == 4:
        data_filter = process_signal.butter_bandpass_filter(data_notch, 7, 13, frequency, 4)
    elif filter_param == 5:
        data_filter = process_signal.butter_bandpass_filter(data_notch, 15, 50, frequency, 4)
    elif filter_param == 6:
        data_filter = process_signal.butter_bandpass_filter(data_notch, 5, 50, frequency, 4)
    return data_filter


def save_data2edf(edf_name, signals, start_date):
    """
    保存数据格式为edf
    """
    if signals.shape[0] == 1:
        channel_names = ['channel1']
    elif signals.shape[0] == 5:
        channel_names = ['channel1', 'channel2', 'channel3', 'channel4', 'channel5']
    elif signals.shape[0] == 8:
        channel_names = ['channel1', 'channel2', 'channel3', 'channel4', 'channel5', 'channel6', 'channel7', 'channel8']
    signal_headers = highlevel.make_signal_headers(channel_names, physical_max=signals.max(), physical_min=signals.min(),
                                                   sample_rate=250, dimension='V')
    header = highlevel.make_header(patientname='X1', gender='F', startdate=start_date)
    print(signals.shape)
    highlevel.write_edf(edf_name, signals, signal_headers, header)
    # highlevel.write_edf_quick(edf_name, signals,250,digital=False)


if __name__ == "__main__":
    file_filter(r'C:\Users\admin\Documents\WeChat Files\wxid_ceg99yq4kkgs22\FileStorage\File\2020-12\kang_data.edf')
