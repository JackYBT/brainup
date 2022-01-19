import os
import numpy as np

def get_rawdata(input_file,data_bits,channel_cnt):

    assert data_bits==12 or data_bits==8, print("get_rawdata(), data_bits != 8 or 12")
    if (data_bits == 12):
        byte_size = 2
    elif (data_bits == 8):
        byte_size = 1

    file = open(input_file, 'rb')
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0, 0)

    sample_count = int(file_size / byte_size / channel_cnt)

    x = np.zeros((sample_count, channel_cnt))

    for i in range(sample_count):
        for j in range(channel_cnt):
            val = 0
            data_bytes = file.read(byte_size)

            for k in reversed(range(byte_size)):
                val = (val << 8) | data_bytes[k]
            # end for

            x[i,j] = val
        # end for
    # end for

    return x

def tmp2data():
    '''
    transfer *.bin to numpy data
    '''
    bit_size = 8
    chan = 8

    tmp_folder = 'participant/bch_1000/test/tmp/'
    rawdata_folder = 'participant/bch_1000/test/data/'
    label_list = os.listdir(tmp_folder)
    for label_name in os.listdir(tmp_folder):
        if label_name.find('.') != -1:continue
        data_path = tmp_folder + label_name + '/'

        for file in os.listdir(data_path):
            if file.find('.bin') == -1:continue
            x = get_rawdata(data_path+file,bit_size,chan)
            np.savez(rawdata_folder+file[:file.find('.')]+'_'+label_name,rawdata=x,label=label_list.index(label_name))

if __name__ == '__main__':
    tmp2data()