from scipy.signal import iirnotch,butter,filtfilt,convolve,hanning
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.ndimage.filters import gaussian_filter1d

def filter_notch(rawdata,f_notch,Q,fs):
    '''
    rawdata: points * channels
    '''
    b,a = iirnotch(f_notch,Q,fs)
    filtdata = filtfilt(b,a,rawdata,axis=0)
    return filtdata

def filter_bandpass(rawdata,f_low,f_high,fs):
    '''
    rawdata: points * channels
    '''
    b,a = butter(3,[f_low,f_high],btype='bandpass',fs=fs)
    filtdata = filtfilt(b,a,rawdata,axis=0)
    return filtdata

def find_gesture(filtdata,fs):
    '''
    filtdata: points * channels
    '''
    assert fs == 1000, 'find_gesture(),fs != 1000'
    time_stamp = []

    # use conv to find max area as gesture
    if fs == 1000:
        window_size = 512
    filtdata_maxpower = np.median(filtdata ** 2,axis=1)
    conv = convolve(filtdata_maxpower,np.ones(window_size))

    alpha = 0.8 # superparameter to cut epoch 
    for i in range(len(conv)):
        if conv[i] > alpha * np.mean(conv) and conv[i-1] < alpha * np.mean(conv):
            time_stamp.append([i-int(window_size/2),i+int(window_size/2)])

    return time_stamp

def preprocess(epoch_folder,data_file,rawdata,label,fs):
    '''
    rawdata: points * channels
    '''
    assert fs == 1000, 'preprocess(), fs != 1000'

    # demean, window
    data_demean = rawdata - np.median(rawdata,axis=0)[np.newaxis,:]
    # data_window = data_demean * (hanning(data_demean.shape[0])[:,np.newaxis])

    # 50Hz notch
    f_notch,Q = 50,35
    filtdata = filter_notch(data_demean,f_notch,Q,fs)

    # bandpass
    f_low,f_high = 1,490
    filtdata = filter_bandpass(filtdata,f_low,f_high,fs)

    # smooth
    filtdata = gaussian_filter1d(filtdata, sigma=1.0, axis=0)

    # find gesture in time courses
    # time_stamp: list, each is [begin,end] of gesture
    time_stamp = find_gesture(filtdata,fs)

    for i in range(len(time_stamp)):
        np.savez(epoch_folder+data_file[:data_file.find('.')]+'_epoch'+str(i),epoch=filtdata[time_stamp[i][0]:time_stamp[i][1],:],label=label)

if __name__ == '__main__':
    fs = 1000
    data_folder = 'participant/bch_1000/data/'
    epoch_folder = 'participant/bch_1000/epoch/'
    for file in os.listdir(data_folder):
        if file.find('.npz') == -1:continue
        npzfile = np.load(data_folder+file)
        rawdata,label = npzfile['rawdata'],npzfile['label']
        preprocess(epoch_folder,file,rawdata,label,fs)