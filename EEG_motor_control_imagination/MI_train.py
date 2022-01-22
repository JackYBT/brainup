import numpy as np
import scipy.io as sio
from scipy.signal import butter, lfilter
from scipy.linalg import sqrtm
from scipy.linalg import inv

def butter_bandpass_filter(signal, lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut/nyq
    high = highcut/nyq
    b,a = butter(order, [low, high], btype='band')
    y = lfilter(b, a, signal, axis=-1)    
    return y

# Create function that could bandpass filtered one subject
def butter_bandpass_one_subject(data, key, lowcut, highcut, fs, interval=None):
    
    # Create new key 'EEG_filtered' to store filtered EEG of each subject
    data[key] = {}
    
    # Current raw EEG
    temp_raw_EEG = data['raw_EEG']
    
    if interval is not None:
        startband = np.arange(lowcut, highcut, step = interval)
        
        for start in startband:
            # This will be new key inside the EEG_filtered
            band = "{:02d}_{:02d}".format(start, start+interval)
            
            # Bandpass filtering
            data[key][band] = {}
            data[key][band]['EEG_all'] = butter_bandpass_filter(temp_raw_EEG, start, start+interval, fs)
            
    else:
        # This will be new key inside the EEG_filtered
        band = "{:02d}_{:02d}".format(lowcut, highcut)
        
        data[key][band]['EEG_all'] = butter_bandpass_filter(temp_raw_EEG, lowcut, highcut, fs)

# covariance and composite covariance
def compute_cov(EEG_data):
    '''
    INPUT:
    EEG_data : EEG_data in shape T x N x S
    
    OUTPUT:
    avg_cov : covariance matrix of averaged over all trials
    '''
    cov = []
    for i in range(EEG_data.shape[0]):
        cov.append(EEG_data[i]@EEG_data[i].T/np.trace(EEG_data[i]@EEG_data[i].T))
        
    cov = np.mean(np.array(cov), 0)
    
    return cov

def decompose_cov(avg_cov):
    '''
    This function will decompose average covariance matrix of one class of each subject into 
    eigenvalues denoted by lambda and eigenvector denoted by V
    Both will be in descending order
    
    Parameter:
    avgCov = the averaged covariance of one class
    
    Return:
    λ_dsc and V_dsc, i.e. eigenvalues and eigenvector in descending order
    
    '''
    λ, V = np.linalg.eig(avg_cov)
    λ_dsc = np.sort(λ)[::-1] # Sort eigenvalue descending order, default is ascending order sort
    idx_dsc = np.argsort(λ)[::-1] # Find index in descending order
    V_dsc = V[:, idx_dsc] # Sort eigenvectors descending order
    λ_dsc = np.diag(λ_dsc) # Diagonalize λ_dsc
    
    return λ_dsc, V_dsc

def white_matrix(λ_dsc, V_dsc):
    '''
    '''
    λ_dsc_sqr = sqrtm(inv(λ_dsc))
    P = (λ_dsc_sqr)@(V_dsc.T)
    
    return P

def compute_S(avg_Cov, white):
    '''
    This function will compute S matrix, S = P * C * P.T

    INPUT:
    avg_Cov: averaged covariance of one class, dimension N x N, where N is number of electrodes
    white: the whitening transformation matrix
    
    OUTPUT:
    S
    '''
    S = white@avg_Cov@white.T
    
    return S

def decompose_S(S_one_class, order='descending'):
    '''
    This function will decompose the S matrix of one class to get the eigen vector
    Both eigenvector will be the same but in opposite order
    
    i.e the highest eigenvector in S left will be equal to lowest eigenvector in S right matrix 
    '''
    # Decompose S
    λ, B = np.linalg.eig(S_one_class)
    
    # Sort eigenvalues either descending or ascending
    if order == 'ascending':
        idx = λ.argsort() # Use this index to sort eigenvector smallest -> largest
    elif order == 'descending':
        idx = λ.argsort()[::-1] # Use this index to sort eigenvector largest -> smallest
    else:
        print('Wrong order input')
    
    λ = λ[idx]
    B = B[:, idx]
    
    return B, λ 

def spatial_filter(B, P):
    '''
    Will compute projection matrix using the following equation:
    W = B' @ P
    
    INPUT:
    B: the eigenvector either left or right class, choose one, size N x N, N is number of electrodes
    P: white matrix in size of N x N 
    
    OUTPUT:
    W spatial filter to filter EEG
    '''
    
    return (B.T@P)

# feature extractions

def compute_Z(W, E, m):
    '''
    Will compute the Z
    Z = W @ E, 
    
    E is in the shape of N x M, N is number of electrodes, M is sample
    In application, E has nth trial, so there will be n numbers of Z
    
    Z, in each trial will have dimension of m x M, 
    where m is the first and last m rows of W, corresponds to smallest and largest eigenvalues
    '''
    Z = []
    
    W = np.delete(W, np.s_[m:-m:], 0)
    
    for i in range(E.shape[0]):
        Z.append(W @ E[i])
    
    return np.array(Z)

def feat_vector(Z):
    '''
    Will compute the feature vector of Z matrix
    
    INPUT:
    Z : projected EEG shape of T x N x S
    
    OUTPUT:
    feat : feature vector shape of T x m
    
    T = trial
    N = channel
    S = sample
    m = number of filter
    '''
    
    feat = []
    
    for i in range(Z.shape[0]):
        var = np.var(Z[i], ddof=1, axis=1)
        varsum = np.sum(var)
        
        feat.append(np.log10(var/varsum))
        
    return np.array(feat)

def load_data(data, start, end, start2, end2, lr, fs=250): 
    all_pos, left_pos, right_pos = 'all_pos', 'left_pos', 'right_pos'  

    data[all_pos] = range(0, data['raw_EEG'].shape[1], 4000)
    data[left_pos] = []
    data[right_pos] = []
    for j in range(len(data[all_pos])):
        if lr:
            if data['etype'][j]==0:
                data[left_pos].append(data[all_pos][j])
            else:
                data[right_pos].append(data[all_pos][j])
        else:
            data[left_pos] = data[all_pos]
            data[right_pos] = data[all_pos]

    # Key to store result
    EEG_left, EEG_right = 'EEG_left', 'EEG_right' 

    # Temporary variable of left and right pos    
    temp_pos_left = data[left_pos]
    temp_pos_right = data[right_pos]

    for band in data['EEG_filtered'].keys():
        temp_EEG_all = data['EEG_filtered'][band]['EEG_all']
        temp_EEG_left = []
        temp_EEG_right = []
        
        # LEFT
        for j in range(len(temp_pos_left)):
            temp_EEG_left.append(temp_EEG_all[:, temp_pos_left[j] + int(start*fs) : temp_pos_left[j] + int(end*fs)])
        data['EEG_filtered'][band][EEG_left] = np.array(temp_EEG_left)
        
        # RIGHT
        for j in range(len(temp_pos_right)):
            temp_EEG_right.append(temp_EEG_all[:, temp_pos_right[j] + int(start2*fs) : temp_pos_right[j] + int(end2*fs)])
        data['EEG_filtered'][band][EEG_right] = np.array(temp_EEG_right)

    return data

def CSP(data, EEG_left, EEG_right, m):

    # Calculate composite covariances
    data['CSP'] = {}
    
    # Iterate over all bands
    for band in data['EEG_filtered'].keys():
        
        # New key to store result
        temp_band = data['CSP'][band] = {}
        
        # Compute left and right covariance
        # LEFT
        temp_band['cov_left'] = compute_cov(data['EEG_filtered'][band][EEG_left])
        
        # RIGHT
        temp_band['cov_right'] = compute_cov(data['EEG_filtered'][band][EEG_right])
        
        # Add covariance of left and right class as composite covariance
        temp_band['cov_comp'] = temp_band['cov_left'] + temp_band['cov_right']

    # white matrices 
    for band in data['EEG_filtered'].keys():
        
        data['CSP'][band]['whitening'] = {}

        temp_whitening = data['CSP'][band]['whitening']
        temp_cov = data['CSP'][band]['cov_comp']

        # Decomposing composite covariance into eigenvector and eigenvalue
        temp_whitening['eigval'], temp_whitening['eigvec'] = decompose_cov(temp_cov)

        # White matrix
        temp_whitening['P'] = white_matrix(temp_whitening['eigval'], temp_whitening['eigvec'])

    # whitening   
    for band in data['EEG_filtered'].keys():
        data['CSP'][band]['S_left'] = {}
        data['CSP'][band]['S_right'] = {}  

        # Where to access data
        temp_P = data['CSP'][band]['whitening']['P']
        Cl = data['CSP'][band]['cov_left']
        Cr = data['CSP'][band]['cov_right']

        # Where to store result
        temp_Sl = data['CSP'][band]['S_left']
        temp_Sr = data['CSP'][band]['S_right']

        # LEFT
        Sl = compute_S(Cl, temp_P)
        temp_Sl['eigvec'], temp_Sl['eigval'] = decompose_S(Sl, 'descending')

        # RIGHT
        Sr = compute_S(Cr, temp_P)
        temp_Sr['eigvec'], temp_Sr['eigval'] = decompose_S(Sr, 'ascending')   

    # Calculate spatial filters   
    for band in data['EEG_filtered'].keys():
        temp_eigvec = data['CSP'][band]['S_left']['eigvec']
        temp_P = data['CSP'][band]['whitening']['P']

        data['CSP'][band]['W'] = spatial_filter(temp_eigvec, temp_P)
        data['train'] = {}
    data['test'] = {}
    
    for band in data['EEG_filtered'].keys():
        data['train'][band] = {}
        data['test'][band] = {} 

        temp_W = data['CSP'][band]['W']
        temp_EEG_left = data['EEG_filtered'][band][EEG_left]
        temp_EEG_right = data['EEG_filtered'][band][EEG_right]

        # LEFT
        data['train'][band]['Z_left'] = compute_Z(temp_W, temp_EEG_left, m)
        data['train'][band]['feat_left'] = feat_vector(data['train'][band]['Z_left'])

        left_label = np.zeros([len(data['train'][band]['feat_left']), 1])
        
        # RIGHT
        data['train'][band]['Z_right'] = compute_Z(temp_W, temp_EEG_right, m)
        data['train'][band]['feat_right'] = feat_vector(data['train'][band]['Z_right'])
        
        right_label = np.ones([len(data['train'][band]['feat_right']), 1])
        
        left  = np.c_[data['train'][band]['feat_left'], left_label]
        right  = np.c_[data['train'][band]['feat_right'], right_label] 
        
        data['train'][band]['feat_train'] = np.vstack([left, right])
        
        np.random.shuffle(data['train'][band]['feat_train'])

    ####################################################
    # Feature Extraction
    ####################################################

    feat_left_all = []
    feat_right_all = []
    
    for band in data['EEG_filtered'].keys():
        # Access LEFT each band
        feat_left = data['train'][band]['feat_left']
        feat_left_all.append(feat_left)
        
        # Access RIGHT each band
        feat_right = data['train'][band]['feat_right']
        feat_right_all.append(feat_right)        
        
    # MERGING (Need to find more efficient method)
    # LEFT
    merge_left = np.zeros(feat_left_all[0].shape)
    for i in feat_left_all:
        merge_left = np.concatenate([merge_left, i], axis=1)  
    # Delete initial zeros
    merge_left = np.delete(merge_left, np.s_[:2*m], axis=1)
    
    # RIGHT
    merge_right = np.zeros(feat_right_all[0].shape)
    for i in feat_right_all:
        merge_right = np.concatenate([merge_right, i], axis=1)  
    # Delete initial zeros
    merge_right = np.delete(merge_right, np.s_[:2*m], axis=1)
    
    # TRUE LABEL
    true_left = np.zeros([merge_left.shape[0], 1])
    true_right = np.ones([merge_right.shape[0], 1])
    
    # FEATURE + TRUE LABEL
    left = np.hstack([merge_left, true_left])
    right = np.hstack([merge_right, true_right])    
    
    # MERGE LEFT AND RIGHT
    train_feat = np.vstack([left, right])    
    np.random.shuffle(train_feat)   
    data['train']['all_band'] = train_feat

    return data

def getEtype(order_path):
    array = []
    for path in order_path:
        array.extend(sio.loadmat(path)['order'])
    return np.ravel(np.array(array))

def train(all_data, all_order, lr=True, lowcut=4, highcut=40, fs=250, start=6, end=12, start2=6, end2=12, m=2):    
 
    # Load EEG data from datapath and store into subj0X variabel then store into ori_dict
    # Then also fetch 's' (EEG data) into mod_data
    data = {}
    data['raw_EEG'] = all_data
    data['etype'] = getEtype(all_order)
    
    key = 'EEG_filtered'
    butter_bandpass_one_subject(data, key, lowcut, highcut, fs, interval=4)   

    # Key to store result
    EEG_left, EEG_right = 'EEG_left', 'EEG_right' 
    data_loaded = load_data(data, start, end, start2, end2, lr)
    data = CSP(data_loaded, EEG_left, EEG_right, m)

    X_train = data['train']['all_band'][:, :-1]
    y_train = data['train']['all_band'][:, -1]

    return X_train, y_train, data

def test(data, eeg_data, lowcut=4, highcut=40, m=2, fs=250):

    key = 'EEG_filtered2'
    butter_bandpass_one_subject(data, key, lowcut, highcut, fs, interval=4)   
    
    Z, feat = {}, {}
    for band in data[key].keys():
        temp_W = data['CSP'][band]['W']
        Z[band] = compute_Z(temp_W, eeg_data, m)
        feat[band] = feat_vector(Z[band])       
        np.random.shuffle(feat[band])
        
    feat_all = []
    
    for band in data[key].keys():
        feature = feat[band]
        feat_all.append(feature)
    
    # MERGING the bands
    merge = np.zeros(feat_all[0].shape)
    for i in feat_all:
        merge = np.concatenate([merge, i], axis=1)   
    # Delete initial zeros
    merge = np.delete(merge, np.s_[:2*m], axis=1)
    
    return merge
