from scipy.interpolate import interp1d
from scipy.signal import butter, lfilter
import numpy as np


def resample(x, y, frequency):
    length = x[-1]
    samples_amount = int(length * frequency)
    period_length = 1 / frequency
    x_new = [period_length *
             i for i in range(samples_amount) if period_length * i >= x[0]]
    y_new = [interp1d(x, y)(i).tolist() for i in x_new]
    return x_new, y_new


def butter_bandpass_filter(data, lowcut, highcut, frequency, order=1):
    nyq = 0.5 * frequency
    low = lowcut / nyq
    high = highcut / nyq

    b, a = butter(order, [low, high], btype='bandpass')
    return lfilter(b, a, data)


def butter_bandstop_filter(data, lowcut, highcut, frequency, order=1):
    nyq = 0.5 * frequency
    low = lowcut / nyq
    high = highcut / nyq

    b, a = butter(order, [low, high], btype='bandstop')
    return lfilter(b, a, data)


def butter_highpass_filter(data, highcut, frequency, order=1):
    nyq = 0.5 * frequency
    high = highcut / nyq
    b, a = butter(order, [high], btype='highpass')
    return lfilter(b, a, data)


def butter_lowpass_filter(data, lowcut, frequency, order=1):
    nyq = 0.5 * frequency
    low = lowcut / nyq
    b, a = butter(order, [low], btype='lowpass')
    return lfilter(b, a, data)


def moving_average(data, n=5):
    ret = np.cumsum(data, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    tail = ret[n - 1:] / n
    head = np.zeros(n-1)
    head[0] = data[0]
    delta = (tail[0] - head[0])/(n-1)
    for i in range(n-2):
        head[i+1] = head[0] + delta * (i + 1)
    return np.concatenate((head, tail))


