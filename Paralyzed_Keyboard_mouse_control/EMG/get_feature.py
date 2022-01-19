import numpy as np
import os
from scipy.signal import hanning
import matplotlib.pyplot as plt

eps = 1e-9

def _get_median_psd(energy_graph, freq_bands, sample_freq, stft_n):
    start_index = int(np.floor(freq_bands[0] / sample_freq * stft_n))
    end_index = int(np.floor(freq_bands[1] / sample_freq * stft_n))
    med_psd = np.median(energy_graph[:, start_index - 1:end_index] ** 2, axis=1)
    return med_psd

def _get_max_psd(energy_graph, freq_bands, sample_freq, stft_n):
    start_index = int(np.floor(freq_bands[0] / sample_freq * stft_n))
    end_index = int(np.floor(freq_bands[1] / sample_freq * stft_n))
    max_psd = np.max(energy_graph[:, start_index - 1:end_index] ** 2, axis=1)
    return max_psd

def get_feature(epoch,fs):
    '''
    epoch: points * channel
    '''
    feature = []
    data_length = epoch.shape[0]
    chan_num = epoch.shape[1]

    w,v = np.linalg.eigh(np.matmul(epoch.T, epoch))
    X = np.matmul(np.matmul(np.diag(w ** (-0.5)),v.T),epoch.T)
    epoch = X.T

    # threshold
    low_threshold = np.sort(epoch,axis=0)[np.floor(data_length / 100.0*3.0).astype(np.int),:]
    high_threshold = np.sort(epoch,axis=0)[-np.floor(data_length / 100.0*3.0).astype(np.int),:]
    for i in range(chan_num):
        epoch[epoch[:,i] > high_threshold[i],i] = high_threshold[i]
        epoch[epoch[:,i] < low_threshold[i],i] = low_threshold[i]
        epoch[:,i] = (epoch[:,i] - np.min(low_threshold)) / (np.max(high_threshold) - np.min(low_threshold))

    # temporal feature
    window_length = 64
    window_step = 32
    window_start = 0
    temp_feature = []
    while window_start + window_length <= data_length:
        window_data = epoch[window_start:window_start + window_length,:]
        # temp_feature.append(np.max(window_data ** 2,axis=0))
        temp_feature.append(np.std(window_data,axis=0))
        # temp_feature.append(np.mean(np.abs(window_data),axis=0))
        window_start += window_step

    temp_feature = np.array(temp_feature) / (np.max(temp_feature,axis=0,keepdims=True) + eps)
    feature.extend(np.array(temp_feature).reshape(-1))
        
    # normalization
    epoch_norm = (epoch - np.mean(epoch,axis=0)[np.newaxis,:]) / np.std(epoch,axis=0)[np.newaxis,:]
    
    epoch_window = epoch_norm * hanning(data_length)[:,np.newaxis]
    fft_data = np.fft.fft(epoch_window.T, n=fs)
    energy_graph = np.abs(fft_data[:, 0: int(fs / 2)])
    freq_bands= [(250,275),(275,300),(300,325),(325,350),(350,375),(375,400),(400,425),(425,450),(450,475),(475,490)]

    freq_feature = []
    for band_index, band in enumerate(freq_bands):
        # feature.extend(_get_median_psd(energy_graph,band,fs,fs) / (np.max(_get_median_psd(energy_graph,band,fs,fs) + eps)))
        freq_feature.append(_get_max_psd(energy_graph,band,fs,fs))
    freq_feature = np.array(freq_feature) / (np.max(freq_feature,axis=1,keepdims=True) + eps)
    feature.extend(freq_feature.reshape(-1))

    feature = np.array(feature)
    return feature

if __name__ == '__main__':
    print('feature()')

