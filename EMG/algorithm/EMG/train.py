from sklearn.svm import LinearSVC,NuSVC
from sklearn.ensemble import RandomForestClassifier
import os
import numpy as np
import random
from get_feature import get_feature
from sklearn.preprocessing import normalize
from sklearn.neighbors import KNeighborsClassifier
from sklearn import manifold

import matplotlib.pyplot as plt

def svm_classifer(train_d, train_l, test_d, test_l):
    model = NuSVC(max_iter=1000)
    model.fit(train_d, train_l)
    test_d_pred = model.predict(test_d)
    acc = model.score(test_d,test_l)
    print(test_l)
    print(test_d_pred)
    print(acc)
    return model,acc

def RF_classifer(train_d, train_l, test_d, test_l):
    model = RandomForestClassifier(n_estimators=300, criterion="gini", max_depth=10, 
                            min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0, 
                            max_features="auto", max_leaf_nodes=None, min_impurity_decrease=0, 
                            min_impurity_split=None, bootstrap=True, oob_score=True, n_jobs=None, 
                            random_state=None, verbose=0, warm_start=False, class_weight=None, 
                            ccp_alpha=0, max_samples=None)
    model.fit(train_d, train_l)
    test_d_pred = model.predict(test_d)
    acc = model.score(test_d,test_l)
    print(test_l)
    print(test_d_pred)
    print(acc)
    return model,acc

def KNN_classifer(train_d, train_l, test_d, test_l):
    model = KNeighborsClassifier(n_neighbors=20, weights='distance', algorithm='auto', leaf_size=30)
    model.fit(train_d,train_l)
    test_d_pred = model.predict(test_d)
    acc = model.score(test_d,test_l)
    prob = model.predict_proba(test_d)
    print(test_l)
    print(test_d_pred)
    print(acc)
    print(prob)
    return model,acc

def visualize(data,label):
    tsne = manifold.TSNE(n_components=2, init='pca')
    X_tsne = tsne.fit_transform(data)
    x_min, x_max = X_tsne.min(0), X_tsne.max(0)
    X_norm = (X_tsne - x_min) / (x_max - x_min)  # 归一化
    y = label
    plt.figure(figsize=(8, 8))
    for i in range(X_norm.shape[0]):
        plt.text(X_norm[i, 0], X_norm[i, 1], str(y[i]), color=plt.cm.Set1(y[i]), 
                 fontdict={'weight': 'bold', 'size': 9})
    plt.xticks([])
    plt.yticks([])
    plt.show()

if __name__ == '__main__':
    
    fs = 1000

    # train data
    label = []
    data = []
    model_epoch = []
    model_label = []

    epoch_folder = 'participant/bch_1000/epoch/'
    for file in os.listdir(epoch_folder):
        if file.find('.npz') == -1:continue
        npzfile = np.load(epoch_folder+file)
        if file.find('_ok_') == -1 and file.find('_thumb_') == -1:
            label.append(npzfile['label'])
            data.append(get_feature(npzfile['epoch'],fs))
            if file.find('epoch0') != -1:
                model_epoch.append(npzfile['epoch'])
                model_label.append(npzfile['label'])
    label = np.array(label)
    data = np.array(data)

    # visualize(data,label)

    model_label = np.array(model_label)

    train_d = data
    train_l = label
    

    # test data

    # calibrate
    calibrate_epoch = []
    calibrate_label = []
    epoch_folder_test = 'participant/bch_1000/test/epoch/'
    for file in os.listdir(epoch_folder_test):
        if file.find('.npz') == -1:continue
        if file.find('_ok_') == -1 and file.find('_thumb_') == -1:
            if file.find('epoch0') != -1:
                npzfile = np.load(epoch_folder_test+file)
                for j in range(1):
                    calibrate_label.append(npzfile['label'])
                    calibrate_epoch.append(npzfile['epoch'])
    calibrate_label = np.array(calibrate_label)
    
    # re-arrange
    # assert model_label.shape == calibrate_label.shape, 'calibrate error'
    # model_idx = np.argsort(model_label)
    # calibrate_idx = np.argsort(calibrate_label)
    # for i in range(len(model_idx)):
    #     if i == 0:
    #         X = model_epoch[model_idx[i]]
    #         Y = calibrate_epoch[calibrate_idx[i]]
    #     else:
    #         X = np.concatenate([X,model_epoch[model_idx[i]]],axis=0)
    #         Y = np.concatenate([Y,calibrate_epoch[calibrate_idx[i]]],axis=0)
    # A = np.matmul(np.linalg.inv(np.matmul(Y.T,Y)),np.matmul(Y.T,X))
    # A = A / np.sum(A,axis=1)[:,np.newaxis]

    label_test = []
    data_test = []
    for file in os.listdir(epoch_folder_test):
        if file.find('.npz') == -1:continue
        if file.find('_ok_') == -1 and file.find('_thumb_') == -1:
            if True: # file.find('epoch0') == -1:
                npzfile = np.load(epoch_folder_test+file)
                label_test.append(npzfile['label'])
                data_test.append(get_feature(npzfile['epoch'],fs))
                # data_test.append(get_feature(np.matmul(npzfile['epoch'],A),fs))
    label_test = np.array(label_test)
    data_test = np.array(data_test)

    # visualize(data_test,label_test)

    model,_ = RF_classifer(train_d, train_l, data_test, label_test)

    idx = np.array([i for i in range(len(label_test))])
    confusion_matrix = np.zeros((12,12))
    for i in range(len(label_test)):

        test_d = data_test[idx == i]
        test_l = label_test[idx == i]
        confusion_matrix[test_l,model.predict(test_d)] += 1
    print(confusion_matrix)