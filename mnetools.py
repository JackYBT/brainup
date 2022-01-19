import json
import time
from mne.time_frequency import psd_array_welch
import numpy as np
import os
import mne

from bledatasend import dataqueue
from data_transfer import DataSend


def get_psd_results(data,sfreq,channel_mount):
    # 特定频段
    FREQ_BANDS = {"delta": [1, 4.5],
                  "theta": [4.5, 8.5],
                  "alpha": [8.5, 11.5],
                  "sigma": [11.5, 15.5],
                  "beta": [15.5, 30]}
    psds, freqs = psd_array_welch(data, sfreq, fmin=0.5, fmax=30.,
                                  n_fft=256, n_overlap=100)
    total_psd = np.sum(psds, axis=-1, keepdims=True)
    # 归一化PSD
    psds /= total_psd
    features=[[] for _ in range(channel_mount)]
    X = []
    # 遍历所有指定的频段，并从psd中获取该频段内的值的均值
    for _, (fmin, fmax) in FREQ_BANDS.items():
        psds_band = psds[:, (freqs >= fmin) & (freqs < fmax)].mean(axis=-1)
        for i in range(channel_mount):
            features[i].append(psds_band[i])
        X.append(psds_band.reshape(len(psds), -1))
    return features
def get_filename(name, directory='records',device_model='formal',save_type=1):
    if save_type==1:
        filename = time.strftime("%Y%m%d-%H%M%S")+'-'+ device_model + '-raw.fif.gz'
    else:
        filename=time.strftime("%Y%m%d-%H%M%S")+'-'+ device_model + '-raw.txt'
    if name:
        path = os.path.join(directory, name)
        os.makedirs(path, exist_ok=True)
        return os.path.join(path, filename)
    else:
        return os.path.join(directory, filename)

def save_file(signal, impedance_data, name, directory,hardWareType,device_model,save_type=1):
    fif_name = get_filename(name, directory, device_model,save_type)
    data = np.array(signal['channels'])
    if save_type==1:
        if hardWareType == '1':
            info = mne.create_info(
                ch_names=['channel1', 'channel2', 'channel3', 'channel4'],
                ch_types=['eeg', 'eeg', 'eeg', 'eeg'],
                sfreq=200
            )
        else:
            info = mne.create_info(
                ch_names=['channel1', 'channel2', 'channel3', 'channel4', 'channel5', 'heart_rate', 'blood_oxygen', 'X',
                          'Y', 'Z'],
                ch_types=['eeg', 'eeg', 'eeg', 'eeg', 'eeg', 'eeg', 'eeg', 'eeg', 'eeg', 'eeg'],
                sfreq=250
            )
        info['description'] = 'imp_data: ' + impedance_data
        raw = mne.io.RawArray(data, info)
        raw.save(fif_name)
    else:
        np.savetxt(fif_name, data, fmt='%f', delimiter=',')
    data_save = DataSend(62, 'success')
    data_save = json.dumps(data_save, default=lambda obj: obj.__dict__, sort_keys=True)
    dataqueue.put(data_save)
    return fif_name