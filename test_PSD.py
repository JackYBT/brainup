import numpy as np
from scipy.fftpack import fft
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

def FFT (Fs,data):
    L = len (data)                        # 信号长度
    N =np.power(2,np.ceil(np.log2(L)))    # 下一个最近二次幂
    FFT_y1 = np.abs(fft(data,int(N)))/L*2      # N点FFT 变化,但处于信号长度
    Fre = np.arange(int(N/2))*Fs/N        # 频率坐标
    FFT_y1 = FFT_y1[range(int(N/2))]      # 取一半
    return Fre, FFT_y1

file_dir = 'temp_cache_10_Second_15hz_cong.npy'
fs = 250
data = np.load(file_dir)
data = data.reshape((-1, 8)).T
data = data[:, 250*2:250*4]
# filt
b, a = signal.butter(4, [9, 30], 'bandpass', fs=250)
data = signal.filtfilt(b, a, data)

b1, a1 = signal.butter(4, [9.5, 10.5], 'bandstop', fs=250)
data = signal.filtfilt(b1, a1, data)

b2, a2 = signal.butter(4, [19.5, 20.5], 'bandstop', fs=250)
data = signal.filtfilt(b2, a2, data)


len_data = data.shape[1]
t = np.linspace(0, len_data//fs, len_data)
#plt.figure(figsize=(15, 8))
h = 4
#plt.plot(t, data[0, :])
#plt.plot(t, 10*h + data[1, :])
#plt.plot(t, 20*h + data[2, :])
#plt.plot(t, 30*h + data[3, :])
#plt.plot(t, 40*h + data[4, :])
#plt.plot(t, 50*h + data[5, :])
#plt.plot(t, 60*h + data[6, :])
#plt.plot(t, 70*h + data[7, :])
#plt.ylim(-200, 500)
#plt.show()

# fft
Fre, FFT_y1 = FFT(fs, data)
fre_avg = []
fft_avg = []
for i in range(8):  
    fre_out, fft_out = FFT(fs, data[0, :])
    fre_avg.append(fre_out)
    fft_avg.append(fft_out)
plt.figure(figsize=(15, 8))

fre_avg = np.mean(np.array(fre_avg),axis=0)
fft_avg = np.mean(np.array(fft_avg),axis=0)

plt.plot(fre_avg,fft_avg)
plt.xlim(0, 50)
plt.grid()
plt.show()