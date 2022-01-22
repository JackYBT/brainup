#!/usr/bin/python3
import argparse
import asyncio
import signal
import threading
import time

import pygame

from callback.client import data_consumer, data_process
from hit import Main
from share.color_print import print_info, print_good
from share.generic import process_number_from_input, CustomError
from util.ble import find_brainUp_bluetooth_hardware, connect_hardware
from util.glob import get_global_value
from util.glob import global_variables_init, set_global_value, err_report, \
    command_queue, data_dump_list, config
from util.queue_monitor import monitor

args = None


def choose_brainUp_device(devices):
    """
    在所发现的脑陆设备中选择最终所需要的设备。
    如果只发现一台脑陆设备，则显示其设备名称和地址。
    如果发现多台脑陆设备，则指示用户选择其所需要的设备。选择完毕后显示所选设备名称及地址。
    """
    length = len(devices)
    if not length:
        raise CustomError("No device found.")

    ret = devices[0]
    if length > 1:
        print_info(f"We've found {length} brainUp devices. Choose one to connect:")
        for i in range(length):
            print_info(f'''Index:\t{i + 1}\tName:\t{devices[i]["name"]}\tAddress:\t{devices[i]["address"]}''')
        input_ok = False
        while not input_ok:
            raw = input("Choose one index to connect: ")
            index, input_ok = process_number_from_input(raw)
            if index - 1 not in range(length):
                input_ok = False
        ret = devices[index - 1]
    print_good(f'''Device name: {ret["name"]}''')
    print_good(f'''Device address: {ret["address"]}''')
    return ret


def set_device_type():
    """指示用户命令行选择设备类型"""
    device_type_d = {1: "k1", 2: "k2s", 3: "mental_oct"}
    print_info("Please tell me what type the device is.")
    for k, v in device_type_d.items():
        print_info(f'''Index:\t{k}\tType:\t{v}''')

    input_ok = False
    while not input_ok:
        raw = input("Choose one index: ")
        index, input_ok = process_number_from_input(raw)
        if index not in device_type_d.keys():
            input_ok = False
    print_good(f'''Device type: {device_type_d[index]}''')
    return device_type_d[index]


def parser_init():
    """设置命令行参数解析规则"""
    parser = argparse.ArgumentParser(description='BrainUp data collection.')
    parser.add_argument('-o', '--output', required=False,
                        dest='is_save_file', action='store_true',
                        help="Whether we should dump data or not.")
    return parser


def sig_int_handler(signum, frame):
    # TODO: 队列变长插入时间 up 两个队列双缓冲轮流来，一分钟 dump ctrl + c 兜底
    """stop collecting (not implemented yet) and dump data"""
    print_info("Termination command accepted.")
    command_queue.append("SIG_INT")
    if args.is_save_file:
        with open(f'''{config["data_dump"]["location"]}/{int(time.time())}.bin''', "wb") as f:
            for raw_data, timestamp in data_dump_list:
                f.write(len(raw_data).to_bytes(1, "big"))
                f.write(raw_data)
                f.write(timestamp.to_bytes(4, "big"))
        print_good("Data dump done. Exit.")
    exit(0)


def signal_handler_init():
    """handle ctrl+c from keyboard."""
    signal.signal(signal.SIGINT, sig_int_handler)
    signal.signal(signal.SIGTERM, sig_int_handler)


async def data_tasks():
    data_consumer_task = asyncio.ensure_future(data_consumer())
    monitor_task = asyncio.ensure_future(monitor())
    err_report_task = asyncio.ensure_future(err_report())
    done, pending = await asyncio.wait([data_consumer_task, monitor_task, err_report_task], )
    for task in pending:
        task.cancel()


def main():
    parser = parser_init()
    global args
    args = parser.parse_args()
    global_variables_init()
    signal_handler_init()

    print_info("Start scanning brainUp devices.")
    devices = find_brainUp_bluetooth_hardware()
    chosen_device = choose_brainUp_device(devices)
    for k, v in chosen_device.items():
        set_global_value(k, v)
    set_global_value("device_type", set_device_type())
    set_global_value("status", "offline")

    # consumer = threading.Thread(target=data_consumer, args=(args.out_file,))
    # for target_func in [connect_hardware, data_process, data_consumer, monitor, err_report]:
    for target_func in [connect_hardware, data_process, data_consumer]:
        target_thread = threading.Thread(target=target_func)
        target_thread.setDaemon(True)
        target_thread.start()

    pygame.init()
    pygame.font.init()
    catchball = Main()
    while True:
        st = get_global_value("status")
        if st == "online":
            catchball.start()
            break
        time.sleep(1)


if __name__ == '__main__':
    main()
