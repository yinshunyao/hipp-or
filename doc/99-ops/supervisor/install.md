# 新环境配置
##  复制服务文件并注册
```shell
sudo cp hipp.service    /usr/lib/systemd/system/hipp.service
sudo systemctl enable hipp
sudo systemctl status hipp
````
##  supervisor的pid和sock在新环境上需要删除，非发布程序
```shell
sudo systemctl restart hipp
sudo systemctl stop hipp
```

# 代码升级
step1: 替换应用程序
step1: 重启服务 systemctl restart hipp

# 可选服务配置更新
如果 datum_defect.service 更新重新拷贝过，执行如下命令
```shell
sudo systemctl daemon-reload
```