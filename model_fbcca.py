import numpy as np
from scipy.signal import iirnotch,cheb1ord,cheby1
from scipy.signal.signaltools import filtfilt
import matplotlib.pyplot as plt



class FBCCA():
    '''
    rawdata: 2-second eeg data, 500 points * 8 channels
    '''
    def __init__(self):
        # init result_cache (slicewindow)
        self.result_cache = []
        
        # param
        self.nFreqStim = 5 # 目标数
        self.channum = 8 # 通道数
        self.freqStim = [12,14,16,18,22]
        self.displayTime = 2
        self.sampleRate=250
        self.nFilterBank = 6

        # FBCCA模板
        self.condY = np.zeros((self.displayTime * self.sampleRate,2*self.nFilterBank,self.nFreqStim))
        n = np.array([ i for i in range(1,self.displayTime*self.sampleRate + 1,1)])[:,np.newaxis] * 1.0 / self.sampleRate
        s = np.zeros((self.displayTime*self.sampleRate,2*self.nFilterBank))
        for ii in range(self.nFreqStim):
            for fb_i in range(int(self.nFilterBank)):
                s[:,2*fb_i:2*fb_i+2] = np.concatenate([np.sin(2.0 * (fb_i + 1) * np.pi * self.freqStim[ii] * n),np.cos(2.0 * (fb_i + 1) * np.pi * self.freqStim[ii] * n)],axis=1)
            # s1 = np.sin(2.0 * np.pi * self.freqStim[ii] * n)
            # s2 = np.cos(2.0 * np.pi * self.freqStim[ii] * n)
            # s3 = np.sin(2.0 * 2.0 * np.pi * self.freqStim[ii] * n)
            # s4 = np.cos(2.0 * 2.0 * np.pi * self.freqStim[ii] * n)
            # s5 = np.sin(2.0 * 3.0 * np.pi * self.freqStim[ii] * n)
            # s6 = np.cos(2.0 * 3.0 * np.pi * self.freqStim[ii] * n)
            # s7 = np.sin(2.0 * 4.0 * np.pi * self.freqStim[ii] * n)
            # s8 = np.cos(2.0 * 4.0 * np.pi * self.freqStim[ii] * n)
            # s9 = np.sin(2.0 * 5.0 * np.pi * self.freqStim[ii] * n)
            # s10 = np.cos(2.0 * 5.0 * np.pi * self.freqStim[ii] * n)
            # s11 = np.sin(2.0 * 6.0 * np.pi * self.freqStim[ii] * n)
            # s12 = np.cos(2.0 * 6.0 * np.pi * self.freqStim[ii] * n)
            # self.condY[:,:,ii] = np.concatenate([s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12],axis=1)
            self.condY[:,:,ii] = s
            self.condY[:,:,ii] = self.condY[:,:,ii] - np.mean(self.condY[:,:,ii],axis=0)

        # filter param
        fs = self.sampleRate / 2.0
        

        # filter
        self.filterBank = []
        freqNotch = 50

        self.filterPre_b,self.filterPre_a = iirnotch(50, 35, fs=self.sampleRate)

        # notch 10 20
        self.filterPre_b1,self.filterPre_a1 = iirnotch(10, 35, fs=self.sampleRate)
        self.filterPre_b2,self.filterPre_a2 = iirnotch(20, 35, fs=self.sampleRate)

        fhp = 90
        fhs = 100
        for nFB in range(self.nFilterBank):
            flp = (nFB+1)*np.min(self.freqStim)-2.0
            fls = (nFB+1)*np.min(self.freqStim)-6.0

            # cheby
            Wp = [flp * 1.0 / fs,fhp * 1.0 / fs]
            Ws = [fls *1.0 / fs, fhs * 1.0 / fs]

            N,Wn = cheb1ord(Wp,Ws,3,30)
            b,a = cheby1(N,0.5,Wn,btype='bandpass')
            self.filterBank.append([b,a])
        
        self.r_threshold = 0.8 # 模板匹配相关性阈值；避免静息状态输出反馈

    '''处理数据'''
    def data_process(self,rawdata):
        # check input
        if (rawdata.shape[0] != self.displayTime * self.sampleRate or rawdata.shape[1] != self.channum):
            print('invalid rawdata')
            return -1,0
        

        bpdatah1 = np.zeros((self.channum,self.displayTime*self.sampleRate))
        bpdatah2 = np.zeros((self.channum,self.displayTime*self.sampleRate))
        bpdatah3 = np.zeros((self.channum,self.displayTime*self.sampleRate))
        bpdatah4 = np.zeros((self.channum,self.displayTime*self.sampleRate))
        bpdatah5 = np.zeros((self.channum,self.displayTime*self.sampleRate))
        bpdatah6 = np.zeros((self.channum,self.displayTime*self.sampleRate))
        for chan in range(self.channum):
            # 50hz陷波
            notchdata = filtfilt(self.filterPre_b,self.filterPre_a,rawdata[:,chan],axis=0)
            # 10 20Hz陷波
            notchdata = filtfilt(self.filterPre_b1,self.filterPre_a1,notchdata,axis=0)
            notchdata = filtfilt(self.filterPre_b2,self.filterPre_a2,notchdata,axis=0)

            lowpassdata = notchdata
            # 各高通
            tempdata = filtfilt(self.filterBank[0][0],self.filterBank[0][1],lowpassdata,axis=0)
            bpdatah1[chan,:] = tempdata
            tempdata = filtfilt(self.filterBank[1][0],self.filterBank[1][1],lowpassdata,axis=0)
            bpdatah2[chan,:] = tempdata
            tempdata = filtfilt(self.filterBank[2][0],self.filterBank[2][1],lowpassdata,axis=0)
            bpdatah3[chan,:] = tempdata
            tempdata = filtfilt(self.filterBank[3][0],self.filterBank[3][1],lowpassdata,axis=0)
            bpdatah4[chan,:] = tempdata
            tempdata = filtfilt(self.filterBank[4][0],self.filterBank[4][1],lowpassdata,axis=0)
            bpdatah5[chan,:] = tempdata
            tempdata = filtfilt(self.filterBank[5][0],self.filterBank[5][1],lowpassdata,axis=0)
            bpdatah6[chan,:] = tempdata

        N = round(self.displayTime * self.sampleRate)

        # FBCCA
        X1 = bpdatah1[:,:N].T
        X2 = bpdatah2[:,:N].T
        X3 = bpdatah3[:,:N].T
        X4 = bpdatah4[:,:N].T
        X5 = bpdatah5[:,:N].T
        X6 = bpdatah6[:,:N].T

        rr2 = np.zeros((6,self.nFreqStim))
        for cond in range(self.nFreqStim):
            r = self.canoncorr(X1,self.condY[:N,:,cond])
            rr2[0,cond] = np.max(r)
            r = self.canoncorr(X2,self.condY[:N,:,cond])
            rr2[1,cond] = np.max(r)
            r = self.canoncorr(X3,self.condY[:N,:,cond])
            rr2[2,cond] = np.max(r)
            r = self.canoncorr(X4,self.condY[:N,:,cond])
            rr2[3,cond] = np.max(r)
            r = self.canoncorr(X5,self.condY[:N,:,cond])
            rr2[4,cond] = np.max(r)
            r = self.canoncorr(X6,self.condY[:N,:,cond])
            rr2[5,cond] = np.max(r)

        # 权重取经验值
        a = 1.25
        b = 0.25
        weights = np.array([i for i in range(1,7,1)]) ** (-a) + b
        rrc = np.matmul(weights[np.newaxis,:],np.multiply(rr2 / (abs(rr2)+1e-9),np.abs(rr2) ** 2))[0]
        index = np.argsort(rrc)
        self.result = index[-1]
        self.corr_max = np.max(rrc)

        return self.result,self.corr_max

    def canoncorr(self,X,Y):
        [Q_X, R_X] = np.linalg.qr(X)
        [Q_Y, R_Y] = np.linalg.qr(Y)
        data_svd = np.dot(Q_X.T,Q_Y)
        [U,S,V] = np.linalg.svd(data_svd)
        return S

    def slicewindow(self):
        if (self.corr_max > self.r_threshold):
            self.result_cache.append(self.result)
        else:
            self.result_cache = []
            return False
        
        # 还没到3次
        if len(self.result_cache) < 3:
            return False
        
        if (self.result_cache[0] == self.result_cache[1] and self.result_cache[1] == self.result_cache[2]):
            self.result_cache = self.result_cache[:-1]
            return True
        elif (self.result_cache[1] == self.result_cache[2]):
            self.result_cache = self.result_cache[1:]
            return False
        else:
            self.result_cache = self.result_cache[2:]
            return False
        


if __name__ == '__main__':
    fbcca = FBCCA()
    fbcca.result_cache = []
    while True:
        result,corr_max = fbcca.data_process(np.sin(2.0 * np.pi * 14 * np.array([i for i in range(1,501,1)])/250)[:,np.newaxis] * np.ones((1,8)))
        fbcca.slicewindow()
        print(fbcca.result_cache)