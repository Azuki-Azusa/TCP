运行代码的方法：
（1）服务器：运行 code\server.py
（2）客户端：运行 code\window.py


客户端可以运行的指令：
lsend [server ip] [local file path] -- send a file to server
lget [server ip] [server file path] -- get a file from server
exit                                             -- exit LFTP


租用的服务器IP地址为134.175.103.254，window默认lsend、lget指令的[server ip]只能是这个IP地址。
如果想在其他主机上运行服务器，需要用编辑器打开window.py，修改第35行的IP地址为测试主机的IP地址即可。