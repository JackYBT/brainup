
import os
import json

with open(os.getcwd() + '/' + 'config.json', 'r') as f:
    json_obj = json.load(f)
config = {}
config['server_ip'] = json_obj['server_ip']
config['server_port'] = json_obj['server_port']
config['save_path'] = json_obj['save_path']
config['com_name'] = json_obj['com_name']
config['bit_rate'] = json_obj['bit_rate']
config['impedance_sever'] = json_obj['impedance_sever']
config['impedance_diff'] = json_obj['impedance_diff']
config['api_server']     = json_obj['api_server']
mode = {'H001':'阿尔兹海默症','H002':'抑郁','H003':'健康采集者', 'H004':'精神分裂'}

def getConfig():
    return config

