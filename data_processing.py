import numpy as np

def data_slither(original_data,shift_lenth,shift_data):
    ret_data=original_data[:,shift_lenth:].copy()
    ret_data=np.append(ret_data,shift_data,axis=1)
    return ret_data