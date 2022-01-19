from converter import conv24bitsToInt, DataSample, DataSatellite
import numpy as np
import time

scale_fac_uVolts_per_count_2gen = 4.5/8388607.0/24*1000*1000
def gen2SamplesGenerate(data):
    samples = []
    str_insert=''
    data_satellite=DataSatellite()
    if len(data) == 84:
        data = data[1:]
    if len(data) != 83:
        print('Wrong size, for raw data' +
              str(len(data)) + ' instead of 83 bytes')
        return None, None,samples

    data_type = data[0]
    if data_type < 49:
        data_satellite.data_type = 3
    else:
        data_satellite.data_type = 2    #阻抗数据

    data_satellite.electric_state=0 # 0 表示没有充电，1表示在充电
    electric_charge = data[82]
    data_satellite.electric_charge=electric_charge*20 #电量

    packetId=data[0]
    heart_rate=data[76]
    blood=data[77]
    accelerometerx=conv8bitToInt8New(data[78])
    accelerometery=conv8bitToInt8New(data[79])
    accelerometerz=conv8bitToInt8New((data[80]))
    data=data[1:]
    for i in range(0, 75, 15):
        ret_str,sample = getSampleDetail(data[i:i + 15], packetId,heart_rate,blood,accelerometerx,accelerometery,accelerometerz)
        if data_type==2:
            data_satellite.imp_data=sample.channel_data

        str_insert=str_insert+ret_str
        samples.append(sample)
        packetId = packetId + 1
    str_insert=str_insert+str(accelerometerx)+','+str(accelerometery)+','+str(accelerometerz)

    return data_satellite, str_insert, samples

def getSampleDetail(dataDetail,packetId,heart_rate,blood,accelerometerx,accelerometery,accelerometerz):
    chan_data = []
    ret_str=''
    for i in range(0, 15, 3):
        chan_data.append(conv24bitsToInt(dataDetail[i:i + 3]))
    chan_data=list(np.array(chan_data)*scale_fac_uVolts_per_count_2gen)
    for i in range(5):
        ret_str = ret_str + str(chan_data[i]) + ','
    chan_data.append(heart_rate)
    chan_data.append(blood)
    chan_data.append(accelerometerx)
    chan_data.append(accelerometery)
    chan_data.append(accelerometerz)
    sample=DataSample(packetId,chan_data,[0, 0, 0],[0, 0, 0, 0, 0],time.perf_counter())
    return  ret_str,sample

def conv8bitToInt8New(byte):
    """ Convert one byte to signed value """

    if byte > 127:
        return (256-byte) * (-1)
    else:
        return byte
