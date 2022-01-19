import numpy as np
import time

from converter import conv24bitsToInt, DataSample, DataSatellite
from converterGen2 import conv8bitToInt8New

scale_fac_uVolts_per_count_3gen = 4.5 / 8388607.0 / 24 * 1000*1000


def gen3SamplesGenerate(data):
    str_insert = ''
    samples = []
    data_satellite=DataSatellite()
    if len(data) != 127:
        print('Wrong size, for raw data' +
              str(len(data)) + ' instead of 127 bytes')
        return None,str_insert,samples
    # data=data[3:]
    data_type = data[0]

    data_satellite.data_type=data_type
    electric_state = data[1]
    data_satellite.electric_state=electric_state
    electric_charge = data[2]
    data_satellite.electric_charge = electric_charge
    packet_id = data[3]
    accelerometer_x = conv8bitToInt8New(data[4])
    accelerometer_y = conv8bitToInt8New(data[5])
    accelerometer_z = conv8bitToInt8New(data[6])
    data_sample = data[7:]
    for i in range(0, 120, 24):
        ret_str, sample = get3SampleDetail(data_sample[i:i + 24],packet_id)
        if data_type==2:
            data_satellite.imp_data=sample.channel_data

        str_insert = str_insert + ret_str
        samples.append(sample)
        packet_id=packet_id+1
    str_insert = str_insert + str(accelerometer_x) + ',' + str(accelerometer_y) + ',' + str(accelerometer_z)
    return data_satellite, str_insert, samples


def get3SampleDetail(dataDetail, packet_id):
    ret_str = ''
    chan_data = []
    for i in range(0, 24, 3):
        chan_data.append(conv24bitsToInt(dataDetail[i:i + 3]))
    chan_data = list(np.array(chan_data) * scale_fac_uVolts_per_count_3gen)
    # print(chan_data)
    for i in range(8):
        ret_str = ret_str + str(chan_data[i]) + ','

    sample = DataSample(packet_id, chan_data, [0, 0, 0], [0, 0, 0, 0, 0], time.perf_counter())
    return ret_str, sample
