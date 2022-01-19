
import numpy as np
import os
# import sh
import json

from collections import Counter
from scipy.fftpack import fft, fftfreq
from scipy import signal
from scipy.ndimage import gaussian_filter
from scipy.ndimage.filters import gaussian_filter1d
from scipy.misc import electrocardiogram
from scipy.signal import find_peaks

from sklearn import model_selection
import joblib
import lightgbm as lgb


FREQ_BANDS = {"delta": [0.5 , 4.5],
              "theta": [4.5 , 8.5],
              "alpha": [8.5 , 11.5],
              "sigma": [11.5, 15.5],
              "beta" : [15.5, 30],
              "gamma": [30  , 100] }

Fs = 200 # sampling rate


def txt2array(filename):
    with open(filename) as f:
        data = f.read().strip().splitlines()
        data = [d.strip() for d in data] #去掉行首行尾空格
        data = [d[1:-1] for d in data]
        data = [d.split(',') for d in data]
        return np.array(data, dtype=np.float64)

    
def preprocess(array):
    # butter filter
    b, a = signal.butter(8, [0.05, 0.5], 'bandpass') 
    data = signal.filtfilt(b, a, array, axis=0)
    # gaussian filter
    data = gaussian_filter1d(data, sigma=1.0, axis=0)
    return data
    
    
def psd_c1(array, Fs=200): # return delta,theta, alpha, sigma, beta, gamma, R for every channel.
    
    rows = len(array)
    freq = fftfreq(rows, 1/Fs)
    
#     fft_value = np.square(np.abs(fft(array)[:int(rows/2+0.5)]))
    fft_value = np.abs(fft(array)[:int(rows/2+0.5)])
    fft_norm = fft_value/(np.sum(fft_value))
    
    # delta
    cond_delta = np.where((freq>=FREQ_BANDS['delta'][0]) &
                          (freq<=FREQ_BANDS['delta'][1]))
    delta = np.sum(fft_norm[cond_delta])
    # theta
    cond_theta = np.where((freq>=FREQ_BANDS['theta'][0]) &
                          (freq<=FREQ_BANDS['theta'][1]))
    theta = np.sum(fft_norm[cond_theta])
    # alpha
    cond_alpha = np.where((freq>=FREQ_BANDS['alpha'][0]) &
                          (freq<=FREQ_BANDS['alpha'][1]))
    alpha = np.sum(fft_norm[cond_alpha])
    # sigma
    cond_sigma = np.where((freq>=FREQ_BANDS['sigma'][0]) &
                          (freq<=FREQ_BANDS['sigma'][1]))
    sigma = np.sum(fft_norm[cond_sigma])
    # beta
    cond_beta = np.where((freq>=FREQ_BANDS['beta'][0]) &
                          (freq<=FREQ_BANDS['beta'][1]))
    beta = np.sum(fft_norm[cond_beta])
    # gamma
    cond_gamma = np.where((freq>=FREQ_BANDS['gamma'][0]) &
                          (freq<=FREQ_BANDS['gamma'][1]))
    gamma = np.sum(fft_norm[cond_gamma])
    
    # R
    R = (alpha + sigma) / beta
    
    return np.array([delta, theta, alpha, sigma, beta, gamma, R])
    

def psd_c4(array, Fs=200):
    res0 = psd_c1(array[:,0], Fs)
    res1 = psd_c1(array[:,1], Fs)    
    res2 = psd_c1(array[:,2], Fs)    
    res3 = psd_c1(array[:,3], Fs)    
    return np.array([res0, res1, res2, res3])


def rectify(array, thr, cnt):
    kv = Counter(array)
    key = sorted(kv.keys())
    for i in range(len(key)-1):
        if key[i] not in kv:
            continue
        for j in range(i+1, len(key)):
            if abs(key[j] - key[i]) > thr:
                break
            kv[key[i]] += kv.pop(key[j])
        if kv[key[i]] < cnt:
            del kv[key[i]]
    for k in list(kv.keys()):
        if kv[k] < cnt:
            del kv[k]
            
    return len(dict(kv)), dict(kv)

def blink_detect(array):
    b, a = signal.butter(8, [0.025, 0.35], 'bandpass') 
    array = signal.filtfilt(b, a, array, axis=0)
    array = array - np.median(array, axis=0, keepdims=True)
    x0 = np.mean(array, axis=1)
    x1 = -x0
    peaks0, r0 = find_peaks(x0, height=[0.02,0.5], prominence=0.02, distance=20, width=4)
    peaks1, r1 = find_peaks(x1, height=[0.02,0.5], prominence=0.02, distance=20, width=4)
    peaks0 = peaks0[(r0['prominences']*r0['widths']>1.1)]
    peaks1 = peaks1[(r1['prominences']*r1['widths']>1.1)]
    length=len(peaks0)+len(peaks1)
    if length>2:
        return 1
    else:
        return 0
    # return len(peaks0)+len(peaks1)
    
    
def test(array): # array is the original eeg signal, which shape is 00x4. 
    cls = joblib.load('./gbm952_0326.pkl') #
    psd = psd_c4(array).reshape(-1, 28) 
    res = cls.predict(psd)
    print(psd)
    

if __name__ == "__main__":
    test()
    
