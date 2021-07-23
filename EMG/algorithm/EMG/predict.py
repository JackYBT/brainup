import numpy as np
from scipy.signal import iirnotch,butter,filtfilt,convolve,hanning
from scipy.ndimage.filters import gaussian_filter1d
from sklearn.ensemble import RandomForestClassifier

from get_feature import get_feature

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
    filtdata_medpower = np.median(filtdata ** 2,axis=1)
    conv = convolve(filtdata_medpower,np.ones(window_size))

    alpha = 0.8 # superparameter to cut epoch 
    for i in range(len(conv)):
        if conv[i] > alpha * np.mean(conv) and conv[i-1] < alpha * np.mean(conv):
            time_stamp.append([i-int(window_size/2),i+int(window_size/2)])

    return time_stamp

def RF_classifer(train_d, train_l):
    model = RandomForestClassifier(n_estimators=300, criterion="gini", max_depth=10, 
                            min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0, 
                            max_features="auto", max_leaf_nodes=None, min_impurity_decrease=0, 
                            min_impurity_split=None, bootstrap=True, oob_score=True, n_jobs=None, 
                            random_state=None, verbose=0, warm_start=False, class_weight=None, 
                            ccp_alpha=0, max_samples=None)
    
    model.fit(train_d, train_l)

    return model

class EMG():
    def __init__(self):
        self.fs = 1000
        self.chan_num = 8
        self.test_length = 512
        self.train_length = 30 * self.fs

    def preprocess(self,rawdata):
        # demean
        data_demean = rawdata - np.median(rawdata,axis=0)[np.newaxis,:]

        # 50Hz notch
        f_notch,Q = 50,35
        filtdata = filter_notch(data_demean,f_notch,Q,self.fs)

        # bandpass
        f_low,f_high = 1,490
        filtdata = filter_bandpass(filtdata,f_low,f_high,self.fs)

        # smooth
        filtdata = gaussian_filter1d(filtdata, sigma=1.0, axis=0)

        return filtdata

    def train(self,train_data,train_label):
        '''
        train_data: labels * points * channels
        '''
        train_data = np.array(train_data)
        assert train_data.shape == (len(train_label),self.train_length,self.chan_num), 'EMG().train(), invalid train_data'

        train_epoch_feature = []
        train_epoch_label = []

        self.label = train_label

        for label_i in range(len(train_label)):
            filtdata = self.preprocess(train_data[label_i,:,:])

            # find gesture in time courses
            # time_stamp: list, each is [begin,end] of gesture
            time_stamp = find_gesture(filtdata,self.fs)

            assert len(time_stamp) > 5, 'EMG().train(), find too few train gestures (5 or less)'
            for i in range(1,len(time_stamp) - 1):
                train_epoch_feature.append(get_feature(filtdata[time_stamp[i][0]:time_stamp[i][1],:],self.fs))
                train_epoch_label.append(train_label[label_i])

            self.model = RF_classifer(train_epoch_feature,train_epoch_label)

    def predict(self,rawdata):
        '''
        rawdata: points * channels
        '''
        rawdata = np.array(rawdata)
        assert rawdata.shape == (self.test_length,self.chan_num), 'EMG().predict(), invalid test rawdata'

        filtdata = self.preprocess(rawdata)

        feature = get_feature(filtdata,self.fs)

        label_i_pred = self.model.predict(feature)

        std_threshold = 1
        if self.H0_test(filtdata,std_threshold) == True:
            label_i_pred = -1

        return label_i_pred

    def H0_test(self,filtdata,std_threshold):
        '''
        H0: std < std_threshold
        '''

        flag = True
        if np.mean(np.std(filtdata,axis=0)) > std_threshold:
            flag = False
        return flag

if __name__ == '__main__':
    emg = EMG()
    