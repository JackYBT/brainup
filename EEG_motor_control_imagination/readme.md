***New update***

data_dump 和 停止采集的潦草实现。

按 ctrl+c，开始 dump data。dump 完毕后程序退出。可使设备关机来告诉他停止收数据（节省电量QAQ）。如果需要再次重新采集数据那就重启一个程序吧 QAQ

dump_data 的目的文件夹可在 config 中配置。

dump 格式为：连续排列的：1 字节原始数据长度（k2s 85，八通道 130，etc.)，大端序的原始数据；4 字节大端序时间戳。

可通过 `tools/binary_dump_reader` 获取原始数据包及接收数据包时的时间信息。

需要解析原始数据包则可调用 `packet_parser` 下对应设备的 `parse_in_detail` 函数获取各通道电压值。

<br>

***当前待办***

快速连接设备

自动判断设备类型

server_process 使用的 demo

<br>

#### Usage

```shell
python3 -m venv vnv
source vnv/bin/activate
pip install -r requirements.txt
./main.py
```
请在 callback 文件夹下 server.py 的 server_process 函数中填入数据包处理逻辑，该函数参数详情请参见 “用户提供代码 -> 数据处理逻辑" 一节。

<br>

#### 文件结构

```shell
.
├── callback
│   ├── client.py # 读取 packet queue 并将数据包发给 server.py
│   ├── rpc_server.py # rpc server，目前可忽略
│   └── server.py # 填入数据包处理代码
├── data # 保存 raw data 所在的文件夹
├── etc
│   └── config.json # 配置文件
├── log # log 文件夹
│   └── brain_up_server.log
├── main.py # 程序入口
├── packet_parser
│   ├── k2s.py # 康睡2 数据包解析，主要功能：判断数据包是否合法；判断是否出现设备电量不足、导联脱落等问题
│   └── mental_oct.py # 精神健康八通道解析，主要功能：判断数据包是否合法
├── readme.md
├── requirements.txt
├── share # 一些杂项功能函数
│   ├── color_print.py
│   └── generic.py
├── tools # 辅助工具
│   ├── binary_dump_reader.py
│   └── generic.py
└── util # 本程序主要功能相关代码
    ├── ble.py
    ├── classifier.py
    ├── glob.py
    └── queue_monitor.py

```

<br>

#### 启动参数

```shell
usage: main.py [-h] [-o file_name]

BrainUp data collection.

optional arguments:
  -h, --help            show this help message and exit
  -o file_name, --output file_name
                        Dump raw data to file. With full path please.
```

**注意：当前情况下处理数据同时进行 dump 会有性能问题，dump 相关功能实际不可用。**

<br>

#### 配置文件

/etc/config.json

```json
{
    "device_warning": { # 在何种情况下发送设备状态相关错误信息。当前只实现了低电量警告。
         "k2s": {
             "low_battery_level": 2 # 电量取值范围 [0, 5]
         },
         "mental_oct": {
             "low_battery_level": 40 # 电量取值范围 [0, 100]
         }
    },
    "rpc": { # 是否使用 rpc。该功能未实现，可忽略
        "use_rpc": false,
        "host": "localhost",
        "port": 8886
    },
    "process_interval": { # 每攒多少个数据包或间隔多久调用算法处理函数。当前只支持“每攒多个数据包”这一逻辑。
        "type": "packet_count", # don't modify
        "value": 5 # 在此处设置。发送给算法处理函数的 data 为 channel_count * (5 * value) 的 np.array
    }
}
```

<br>

#### 如何使用

<br>

###### 准备阶段

启动程序后程序会自动收缩带有 `brain` 相关字样的蓝牙设备。如果搜索到多个蓝牙设备，会要求用户在命令行显式指定连接哪一台设备（输入屏幕上打印的设备 index 进行选择）。目前启动一个程序实例只允许同时连接一台设备。

```shell
[+] Start scanning brainUp devices.
[+] We've found 2 brainUp devices. Choose one to connect:
[+] Index:	1	Name:	BRAIN-AHB-51855F02	Address:	166BA30C-6A13-414F-9C5C-6A6904200077
[+] Index:	2	Name:	BRAIN-AHB-51855EF6	Address:	5090256D-AD60-47E5-A2C6-FE74676EDD33
Choose one index to connect: 
```

如果只检测到一台脑陆设备则无需进行选择。设备确定后屏幕上显示设备相关信息，并要求用户指定设备种类（输入屏幕上打印的设备 index 进行选择）。目前不支持对康1 设备的设备。

```shell
[+] Device name: BRAIN-AHB-51855F02
[+] Device address: 166BA30C-6A13-414F-9C5C-6A6904200077
[+] Please tell me what type the device is.
[+] Index:	1	Type:	k1 # 康睡 1
[+] Index:	2	Type:	k2s # 康睡 2 
[+] Index:	3	Type:	mental_oct # 精神健康八通道
Choose one index: 
```

选择设备型号后，程序会连接该设备。当设备佩戴完毕后，可在屏幕上输入 `y` 或键入回车指示程序开始数据收集：

```shell
[+] Start connecting to device. Might take a while.
[+] Device connected.
Press enter or type 'y' when you're ready: 
```

注意对于任何一处需要输入的地方，如果输入不合法（如选择 index 时输入了超出 index 范围的值），程序会要求用户重复输入直至输入正确为止。

<br>

###### 数据收集阶段

当前每收到一个原始数据包，程序会记录收到该数据包的时间并将所接收数据包通过调用 server.py 中 server_process 函数进行处理。可将数据处理流程填入该函数。

```python
def server_process(
        data_matrix, first_packet_recv_time_in_second, is_train_data,
        device_type, device_id, task_type, interval_type, interval_value)
```

对于数据处理函数的详细参数信息，请见 “用户提供代码” 一节。

<br>

###### 异常状态

如果出现设备出现低电量等问题，则会在屏幕上打印报错信息。注意目前报错信息只显示一次：

```shell
[-] Low battery.
```

如果发生数据堆积，则队列中数据包数量每超过 100 则会在屏幕上打印当前队列长度及时间：

```shell
[-] Data_queue length: 400, 17:15:42
[-] Data_queue length: 600, 17:15:46
[-] Data_queue length: 700, 17:15:48
```

<br>

#### 用户提供代码

目前设计有两个函数需有用户自行提供处理代码：数据处理逻辑及异常处理逻辑。

**异常处理逻辑尚未实现**

<br>

###### 数据处理逻辑

```python
def server_process(
        data_matrix, first_packet_recv_time_in_second, is_train_data,
        device_type, device_id, task_type, interval_type, interval_value):
    """
    :param data_matrix:
        行数为 channel_count、列数为总采集次数的 np.array
        总采集采集次数为每次调用本函数时的数据包间隔数（config 中配置的 process_interval.value）乘以每个数据包对应的采集次数（5）
        该二维数组中每个数据均为浮点类型，表示 EEGV（每个通道最终测量值），单位为uV。
    :param first_packet_recv_time_in_second:
        收到第一个数据包时的时间戳，精确至秒
        目前协议中无时间戳信息，故使用接收时的时间戳；在硬件协议更新后会修正为发送时的时间戳
    :param is_train_data:
        bool 是否为训练数据。0 表示否 1 表示是。
    :param device_type:
        表示设备类型的字符串。
        取值范围：["k1", "k2s", "mental_oct"]
        分别对应：康睡一代，康睡二代，精神健康八通道
    :param device_id:
        设备名称。字符串。形如 "BrainUp70B4AE2C831"
    :param task_type:
    :param interval_type:
        config 中的 process_interval.type 所填入的字符串
        当前唯一取值为 "packet_count"
    :param interval_value:
        config 中的 process_interval.value 所填入的正整数

    :return:
        希望本程序执行的下一步命令。当前该功能尚未实现，return 0 即可。
    """
    return 0
```

<br>

###### 异常处理逻辑

```python
def status_notify(device_type, device_id, status_code, full_message):
    """
    :param device_type: 设备类型
    :param device_id: 设备 ID（当前用设备名称代替）
    :param status_code: 状态代码。具体格式及内容待定。
    :param full_message: 详细描述信息。为可读文本。
    :return: 希望本程序执行的下一步命令，如指示本程序向蓝牙设备发送指令告知其停止数据采集。格式待商议。
    """
    return 0
```

<br>

#### 数据结构

<br>

##### 接收数据包队列

定义在：`util/glob.py -> bluetooth_data_queue = deque(maxlen=5000)`

双向队列，溢出时自动覆盖最先入队（最老）数据。

生产者线程：hardware_communicator

消费者线程：data_queue_consumer

monitor 线程：data_queue_monitor

<br>

##### 攒包队列

定义在：`callback/client.py -> tiny_queue = queue.Queue(配置文件中定义的攒包个数)`

生产者线程：data_queue_consumer

消费者线程：sub_queue_consumer

<br>

##### 错误信息字典

定义在：`util/glob.py -> err_report_d = {}`

+ Key: 错误描述字符串
+ Value: {"always": False, "reported": False} always 表示为否表示报错信息只显示一次

生产者线程：hardware_communicator

消费者线程：error_reporter

<br>

#### 子线程列表

<br>

##### hardware_communicator

执行函数：`util/ble.py -> connect_hardware`

功能：接收控制指令（该功能尚未实现）并向硬件设备发送控制指令；接收硬件回传数据并将合法数据放入接收数据包队列。

是否为守护线程：是

父线程：main

<br>

##### error_reporter

执行函数：`util/glob.py -> err_report`（放在这里主要是为了防止循环 import，之后代码位置会调整）

功能：读取其他线程产生的错误信息（非异常信息）并将其打印在屏幕上。

是否为守护线程：是

父线程：main

<br>

##### data_queue_monitor

执行函数：`util/queue_monitor.py -> monitor`

功能：当接收数据包队列中出现堆积时在屏幕上打印告警（当堆积 item 长度为 100 的倍数时打印）。

是否为守护线程：是

父线程：main

<br>

#####data_queue_consumer

执行函数：`callback/client.py -> data_consumer`

功能：将所接收的数据包放入攒包队列中以供 sub_queue_consumer 消费。如果攒包队列已满则等待至 sub_queue_consumer 将该队列清空。如果该线程一直处于等待攒包队列清空的状态，则接收数据包的队列将出现堆积。

是否为守护线程：是

父线程：main

<br>

##### sub_queue_consumer

执行函数：`callback/client.py -> data_process`

功能：当所攒数据包等于 config 中所设置的阈值时，处理数据包内容并将其作为参数传递给 server_process

是否为守护线程：是

父线程：data_queue_consumer

<br>

#### 辅助工具

位于 tools 文件夹下，提供了一些辅助函数。

<br>

###### 将原始数据包转化为十进制字符串

```python
# generic.py -> bytes_2_decimal_str
# 输入
b'##>\x03\x00\x00\x06\x00\x00\xaf\x00\x06\x9d\x00\r\xce\x00\x05*\x00\x05\xc6\x00\x04\xce\x00\x05Y\x00\x03\xf0\x00\x0e\\\x00\x08K\x00\x10\xdb\x00\x06\x07\x00\x06z\x00\x05\x94\x00\x05"\x00\x04\x00\x00\x0f\x84\x00\x04\xd0\x00\x03\xa1\x00\x03w\x00\x02\xf8\x00\x06H\x00\x05\t\x00\x03\xc8\x00\x00d\x00\x00\xd4\xff\xf8@\x00\x00\xef\x00\x00!\x00\x05\xba\x00\x053\x00\x03z\xff\xf6?\x00\x01\xf5\xff\xfeb\x00\x02\x12\x00\x01\xca\x00\x04\xe5\x00\x05Y\x00\x03\x88\xff\xfe\xbe'

# 输出
"35 35 62 3 0 0 6 0 0 175 0 6 157 0 13 206 0 5 42 0 5 198 0 4 206 0 5 89 0 3 240 0 14 92 0 8 75 0 16 219 0 6 7 0 6 122 0 5 148 0 5 34 0 4 0 0 15 132 0 4 208 0 3 161 0 3 119 0 2 248 0 6 72 0 5 9 0 3 200 0 0 100 0 0 212 255 248 64 0 0 239 0 0 33 0 5 186 0 5 51 0 3 122 255 246 63 0 1 245 255 254 98 0 2 18 0 1 202 0 4 229 0 5 89 0 3 136 255 254 190"
```

<br>

#### 已知问题

<br>

##### 设备连接卡慢

周围蓝牙设备较多时可能出现搜索不到设备或与设备建立连接前需等待很久的问题。经询问 @李寒辉 老师，使用蓝牙串口并不能解决这一问题。

建议在会议室等干扰较小的地方使用本代码。如果搜索不到设备，可尝试多起几次本程序。

**解决方式**：bleak==0.9.1

<br>

##### 搜索不到设备


<br>

#### TODO

- [ ] 暂停、中止与恢复数据采集
- [ ] 为啥子蓝牙连接那么的慢 QAQ
- [ ] 原始数据落盘
- [ ] 线程安全
- [ ] 鉴权
- [ ] windows 适配：彩色打印乱码
- [ ] 之后可能通讯选择 wifi
- [ ] 信号弱搜索不到
- [ ] 设备类型自动识别
- [ ] 同时跑多个实例会不会出现蓝牙传输失败的情况

<br>

#### 需求列表

- [x] （袁碧添）每隔多长时间或多少个数据包调用一次处理算法
- [ ] （袁碧添）调用参数标明是否为训练数据

<br>

#### 打断点

断点 notification_handler 看所接收到的原始数据
断点 server_process 看算法函数收到的参数
