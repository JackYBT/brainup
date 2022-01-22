import numpy as np
import scipy.io as sio
from scipy.fftpack import fft
from scipy.signal import butter, lfilter
import sklearn

def subjectCounter(i):
    return 'subject0{}'.format(i)

def butter_bandpass_filter(signal, lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    y = lfilter(b, a, signal, axis=-1)

    return y

def train():
    # Number of subject
    ns = 15
    data = dict()
    ns += 1
    # Iter over all data path then store them in sub0X variable
    for i in range(1, ns):
        data_path = 'C:/Users/Ziyi Yang/Desktop/MI models/FBCSP/data/data{}.mat'.format(i)
        subj = subjectCounter(i)

        # Load EEG data from datapath and store into subj0X variabel then store into ori_dict
        # Then also fetch 's' (EEG data) into mod_data
        data[subj] = {}
        data[subj]['raw_EEG'] = sio.loadmat(data_path)['data_all']

    # Bandpass filtering all subject
    lowcut = 4
    highcut = 30
    fs = 250

    # Iterate over all subjects
    for i in range(1, ns):
        subj = subjectCounter(i)
        data[subj]['EEG_filtered'] = {}
        temp_raw_EEG = data[subj]['raw_EEG']
        data[subj]['EEG_filtered']['EEG_all'] = butter_bandpass_filter(temp_raw_EEG, lowcut, highcut, fs)

    all_pos = 'all_pos'

    resting_start = 4
    resting_end = 6
    start = 8
    end = 12

    for i in range(1, ns):
        subj = subjectCounter(i)
        # Temporary variable of left and right pos
        data[subj][all_pos] = range(0, data[subj]['raw_EEG'].shape[1], 4000)
        temp_pos = data[subj][all_pos]

        temp_EEG_all = data[subj]['EEG_filtered']['EEG_all']
        temp_EEG_MI = []
        temp_EEG_resting = []

        # MI
        for j in range(len(temp_pos)):
            temp_EEG_MI.append(temp_EEG_all[:, temp_pos[j] + int(start * fs): temp_pos[j] + int(end * fs)])
        data[subj]['EEG_filtered']['EEG_MI'] = np.array(temp_EEG_MI)

        # Resting
        for j in range(len(temp_pos)):
            temp_EEG_resting.append(temp_EEG_all[:, temp_pos[j] + int(resting_start * fs): temp_pos[j] + int(resting_end * fs)])
        data[subj]['EEG_filtered']['EEG_resting'] = np.array(temp_EEG_resting)


    power_band_start, power_band_end = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19], [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

    # calculate power
    for jj in range(len(power_band_start)):
        for i in range(1, ns):
            subj = subjectCounter(i)
            power_MI = np.zeros((data[subj]['EEG_filtered']['EEG_MI'].shape[0], 8))
            power_resting = np.zeros((data[subj]['EEG_filtered']['EEG_resting'].shape[0], 8))

            # power_MI
            for j in range(data[subj]['EEG_filtered']['EEG_MI'].shape[0]):

                for k in range(0, 8):
                    temp_EEG_MI = data[subj]['EEG_filtered']['EEG_MI']
                    temp_MI_fft = fft(temp_EEG_MI[j, k, :])
                    df = fs / len(temp_MI_fft)
                    f = np.arange(0, fs - df, df)
                    temp_power = abs(temp_MI_fft) ** 2 / (len(temp_MI_fft) * fs)
                    temp_power2 = np.mean(temp_power[int((power_band_start[jj]+df)/df): int((power_band_end[jj]+df)/df)])
                    if temp_power2 > 10:
                        power_MI[j, k] = 0
                    else:
                        power_MI[j, k] = temp_power2
            data[subj]['power_MI_{:02d}_{:02d}'.format(power_band_start[jj], power_band_end[jj])] = np.array(power_MI)

            # power_resting
            for j in range(data[subj]['EEG_filtered']['EEG_resting'].shape[0]):

                for k in range(0, 8):
                    temp_EEG_resting = data[subj]['EEG_filtered']['EEG_resting']
                    temp_resting_fft = fft(temp_EEG_resting[j, k, :])
                    df = fs / len(temp_resting_fft)
                    f = np.arange(0, fs - df, df)
                    temp_power = abs(temp_resting_fft) ** 2 / (len(temp_resting_fft) * fs)
                    temp_power2 = np.mean(temp_power[int((power_band_start[jj] + df) / df): int((power_band_end[jj] + df) / df)])
                    if temp_power2 > 10:
                        power_resting[j, k] = 0
                    else:
                        power_resting[j, k] = temp_power2
            data[subj]['power_resting_{:02d}_{:02d}'.format(power_band_start[jj], power_band_end[jj])] = np.array(power_resting)

            # label
            c1 = np.ones((1, len(data[subj]['power_MI_{:02d}_{:02d}'.format(power_band_start[jj], power_band_end[jj])])), dtype=np.int32)
            c2 = np.zeros((1, len(data[subj]['power_resting_{:02d}_{:02d}'.format(power_band_start[jj], power_band_end[jj])])), dtype=np.int32)
            c3 = np.concatenate([c1, c2])
            data[subjectCounter(i)]['etype'] = np.ravel(np.array(c3))


    acc = np.zeros((len(power_band_start), ns-1))
    for jj in range(len(power_band_start)):
        for i in range(1, ns):
            subj = subjectCounter(i)

            x1 = data[subj]['power_MI_{:02d}_{:02d}'.format(power_band_start[jj], power_band_end[jj])]
            x2 = data[subj]['power_resting_{:02d}_{:02d}'.format(power_band_start[jj], power_band_end[jj])]
            x = np.concatenate([x1, x2])
            x = x[:, [1, 2, 3, 4, 5, 6, 7]]
            y = data[subjectCounter(i)]['etype']
            train_data, test_data, train_label, test_label = sklearn.model_selection.train_test_split(x,
                                                                                                    y,
                                                                                                    train_size=0.8,
                                                                                                    test_size=0.2)
            # 中位数
            index1 = 0
            index0 = 0
            for ii in range(len(train_data)):
                if train_label[ii] == 1:
                    index1 += 1
                else:
                    index0 += 1
            train_MI_test = np.zeros((index1, 7))
            train_resting_test = np.zeros((index0, 7))
            index1_1 = 0
            index0_1 = 0
            for ii in range(len(train_data)):
                if train_label[ii] == 1:
                    train_MI_test[index1_1, :] = train_data[ii]
                    index1_1 += 1
                else:
                    train_resting_test[index0_1, :] = train_data[ii]
                    index0_1 += 1

            range_up_all = np.zeros((1, 7))
            range_down_all = np.zeros((1, 7))
            for kk in range(0, 7):
                range_up_all[0, kk] = np.median(train_MI_test[:, kk])
                range_down_all[0, kk] = np.median(train_resting_test[:, kk])

            threshold = (range_up_all + range_down_all) / 2

            acc_num = 0
            for ii in range(len(test_data)):
                acc1 = 0
                acc2 = 0
                for kk in range(0, 7):
                    if test_data[ii, kk] > threshold[0, kk]:
                        acc1 = acc1 + 1
                    else:
                        acc2 = acc2 + 1
                if acc1 > acc2:
                    label = 1
                else:
                    label = 0
                if label == test_label[ii]:
                    acc_num = acc_num + 1
            acc[jj, i-1] = acc_num / ii

    for i in range(1, ns):
        acc_end = np.max(acc[i-1, :])
        local_max = np.argmax(acc[i-1, :])
        # print("Subject{:02d} : {:.2f} %   band : {}_{}Hz".format(i, acc_end * 100, power_band_start[local_max], power_band_end[local_max]))


def test():
    lowcut = 4
    highcut = 30
    fs = 250
    power_band_start, power_band_end = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19], [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]


    # 滤波
    test_filter = butter_bandpass_filter(eeg_data, lowcut, highcut, fs)

    # 计算 power
    test_power = np.zeros((1, 8))
    for k in range(0, 8):
        test_fft = fft(test_filter[k, :])
        df = fs / len(test_fft)
        f = np.arange(0, fs - df, df)
        temp_power = abs(test_fft) ** 2 / (len(test_fft) * fs)
        test_power[0, k] = np.mean(temp_power[int((power_band_start[local_max] + df) / df): int((power_band_end[local_max] + df) / df)])

    for kk in range(0, 7):
        if test_power[0, kk] > threshold[0, kk]:
            acc1 = acc1 + 1
        else:
            acc2 = acc2 + 1
    if acc1 > acc2:
        label = 1
    else:
        label = 0
