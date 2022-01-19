import numpy as np
from scipy.fftpack import fft
import mne
import scipy.signal as signal

def ArrayConversion(List):
    SingleArray = np.array(List)
#     Array = SingleArray.reshape(8,-1)
#     print(SingleArray.shape)
    return  SingleArray

def Bandpass(x,Wn,low_freq,high_freq,fs):
    b, a = signal.butter(Wn, [low_freq,high_freq], 'bandpass',fs = fs)
    Temp = []
    for i in range(x.shape[0]):
        SingleDataFilt = signal.filtfilt(b,a,x[i])
        Temp.append(SingleDataFilt)
    return ArrayConversion(Temp)

# 输入滤波后EEG

def SingleChPSD(fs,data): 
    Y = fft(data)
    num_fft  = len(data)
    freqs = np.linspace(0,fs/2,len(data)//2+1)
    theta =   [4,   8]
    alpha_L = [8,   9]
    alpha_M = [9,  11]
    alpha_H = [11, 13]

    beta_L =  [14,  19]
    beta_M =  [19,  24]
    beta_H =  [24,  30]

    freqs_band = [theta,alpha_L,alpha_M,alpha_H, beta_L, beta_M, beta_H]
    PSD = []
    for choose_band in freqs_band:
        choose_ps = Y[np.where(np.logical_and(np.greater_equal(freqs,choose_band[0]),np.less_equal(freqs,choose_band[1])))]
        ps = abs(choose_ps)**2/num_fft 
        PSD.append(np.sum(ps))
    PSD = np.array(PSD)
    return PSD

# main(1)

## main(1)
def data_freqs_sorted(file_edf):
    
    raw = mne.io.read_raw_edf(file_edf)
    data, _ = raw[:, :]
    n_chal, n_samp = data.shape
    PSD_value_list = []
    Bandpass(data,5,0.5,40,250)

    for i in range(n_chal):
        PSD_value = SingleChPSD(250,data[i, :])
        PSD_value_list.append(PSD_value)
    PSD_mean = np.mean(np.array(PSD_value_list), 0)
    PSD_mean = PSD_mean / np.mean(PSD_mean)

    PSD_dict_all = {'Theta':PSD_mean[0], 'Alpha':PSD_mean[1]+PSD_mean[2]+PSD_mean[3],'Beta':PSD_mean[4]+PSD_mean[5]+PSD_mean[6]}
    d_order_all=sorted(PSD_dict_all.items(),key=lambda x:x[1],reverse=True) 

    PSD_dict_Alpha = {'Alpha_L':PSD_mean[1], 'Alpha_M':PSD_mean[2], 'Alpha_H':PSD_mean[3]}
    PSD_dict_Beta = {'Beta_L':PSD_mean[4],'Beta_M':PSD_mean[5],'Beta_H':PSD_mean[6]}

    d_order_Alpha=sorted(PSD_dict_Alpha.items(),key=lambda x:x[1],reverse=True) 
    d_order_Beta=sorted(PSD_dict_Beta.items(),key=lambda x:x[1],reverse=True) 

    d_order_all_new = dict(d_order_all)
    # d_order_all_new['Alpha'] = d_order_Alpha[0][1]
    # d_order_all_new['Beta'] = d_order_Beta[0][1]
    
    freq_Theta = [4, 8]
    if d_order_Alpha[0][0]=='Alpha_L':
        freq_Alpha = [8, 9]
    elif d_order_Alpha[0][0]=='Alpha_M':
        freq_Alpha = [9, 11]
    else:
        freq_Alpha = [11, 13]


    if d_order_Beta[0][0]=='Beta_L':
        freq_Beta = [14, 19]
    elif d_order_Beta[0][0]=='Beta_M':
        freq_Beta = [19, 24]
    else:
        freq_Beta = [24, 30]
    
    #  return
    # index-0: 不同频率能量从达到小排序（字典形式），index-1：theta对应的频率， index-2：alpha对应频率， index-3：beta对应频率
    return n_chal, d_order_all_new, freq_Theta, freq_Alpha, freq_Beta

## 信号滤波

def data_filter(data_in, freq_band, fs):
    '''
    data_in: input data
    freq_band: [freq_low, freq_high]
    
    fs: sample rate
    '''
    b, a = signal.butter(4, freq_band, 'bandpass', fs=fs)
    data_out = signal.filtfilt(b, a, data_in)
    
    return data_out    

# main(2)

#1.  load 8 channel data
def data_amplitude(raw_edf_file):
    
    raw = mne.io.read_raw_edf(raw_edf_file)
    fs = raw.info['sfreq']  # fs: sample rate

    data, _ = raw[:, :]  # data (8, sample)
    n_chal, n_samp = data.shape  # n_chal: 通道数， n_sample：采样点数
    n_time = n_samp / fs  # n_time: 数据时长

    # 2. filter data
    freq_delta = [0.3, 3.5]
    freq_theta = [4, 7.5]
    freq_alpha = [8, 13]
    freq_beta = [14, 30]

    data_filt_delta = data_filter(data, freq_delta, fs)
    data_filt_theta = data_filter(data, freq_theta, fs)
    data_filt_alpha = data_filter(data, freq_alpha, fs)
    data_filt_beta = data_filter(data, freq_beta, fs)
    
    # 3. sort data amplitude
    amplitude_delta = np.mean([np.percentile(np.sort(abs(data_filt_delta[i, :])), 90) for i in range(n_chal)])
    amplitude_theta = np.mean([np.percentile(np.sort(abs(data_filt_theta[i, :])), 90) for i in range(n_chal)])
    amplitude_alpha = np.mean([np.percentile(np.sort(abs(data_filt_alpha[i, :])), 90) for i in range(n_chal)])
    amplitude_beta = np.mean([np.percentile(np.sort(abs(data_filt_beta[i, :])), 90) for i in range(n_chal)])
    
    # 4. return 
    # index-0: theta 波幅  index-1 alpha 波幅  index-2: beta 波幅
    return amplitude_theta, amplitude_alpha, amplitude_beta

# # main()

# file_edf = '2021-03-25_15-22-47.edf'

# n_chal,d_order_all_new, freq_Theta, freq_Alpha, freq_Beta = data_freqs_sorted(file_edf)

# amplitude_theta, amplitude_alpha, amplitude_beta = data_amplitude(file_edf)

# print()
# print()
# print(n_chal,d_order_all_new, freq_Theta, freq_Alpha, freq_Beta)
# print()
# print()
# print(amplitude_theta, amplitude_alpha, amplitude_beta)



