from socket import *
import threading

import os
import stat

import sender
import receiver

class client():
    def __init__(self, cmd, host, filepath):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.host = host
        self.filepath = filepath
        self.port = 23333
        self.bufsize = 1024
    def run(self):
        if (self.cmd == "lsend"):
            self.send()
        else:
            self.get()
        
    
    def send(self):
        dst = (self.host, self.port)
        info = os.lstat(self.filepath)
        fileSize = info.st_size

        #握手需要的基本信息
        cmd = bytes("send", encoding = 'utf-8')
        filename = self.filepath.split('/')[-1].split('\\')[-1] # split the path to get the filename
        filename = bytes(filename, encoding = 'utf-8')
        flSize = bytes(str(fileSize), encoding='utf-8')
        request = cmd + b'\n' + filename + b'\n' + flSize

        # send the command and filepath to server
        udpClient = socket(AF_INET, SOCK_DGRAM)
        udpClient.sendto(request, dst)
        
        #等待服务器新线程分配的端口地址
        print("Waiting for addr")
        newPort, addr = udpClient.recvfrom(self.bufsize)
        newPort = int(str(newPort, encoding = 'utf-8'))
        newAddr = (self.host, newPort)

        SENDER = sender.TCPsender()
        SENDER.sendPacket(udpClient, newAddr, self.filepath, fileSize)

    
    def get(self):
        udpClient = socket(AF_INET, SOCK_DGRAM)
        dst = (self.host, self.port)
        cmd = "get"
        cmd = bytes(cmd, encoding = 'utf-8')
        request = cmd + b'\n' + bytes(self.filepath, encoding = 'utf-8') + b'\n' + bytes(str(0), encoding='utf-8')

        # send the command and the path of file to server
        udpClient.sendto(request, dst)

        #addr为服务器新线程的端口地址
        print ("Waiting for addr")
        newPort, addr = udpClient.recvfrom(self.bufsize)
        newPort = int(str(newPort, encoding = 'utf-8'))
        addr = (self.host, newPort)
        print(addr)

        try:
            data = udpClient.recv(self.bufsize)
        except BaseException as e:
            print(e)
            print("Sever has been closed.")
        else:
            data, fileSize = data.split(b'\n', 1)
            data = str(data, encoding = 'utf-8')
            fileSize = int(str(fileSize, encoding = 'utf-8'))
            if (data == "N") :
                # no file under the path
                print("No this file in server.")
            else:
                ready = bytes("Y", encoding = 'utf-8')
                udpClient.sendto(ready, addr)
                filename = self.filepath.split('/')[-1].split('\\')[-1]
                while os.path.isfile(filename) :
                    if filename.find('.') == -1 :
                        filename = filename + "_2"
                    else :
                        name, postfix = filename.split('.')
                        name = name + "_2"
                        filename = name + "." + postfix
                    
                RECEIVER = receiver.TCPreceiver()
                RECEIVER.receivePacket(udpClient, filename, fileSize)