
## Create data directory
```
在brain_hat目录下新建data目录
在data目录下新建edf目录
```

## 修改 websocket服务ip 和端口

```
修改config.json文件中的server_ip 和server_port
```



## 启动websocket服务

```
运行 websocketServerTest文件
```

## 打包成exe程序
```
pyinstaller -D websocketServerTest
or
pyinstaller -D --clean --onedir --onefile -i favicon.ico websocketServerTest.py
```

config.json

api_server
测试环境为http://101.200.216.197:9011
生产环境为http://39.105.199.223:9011

