from socket import *
from time import ctime
import threading

import os
import stat

import sender
import receiver
 
def send(newSocket, filename, fileSize):
    while os.path.isfile(filename) :
        if filename.find('.') == -1 :
            filename = filename + "_2"
        else :
            name, postfix = filename.split('.')
            name = name + "_2"
            filename = name + "." + postfix
    RECEIVER = receiver.TCPreceiver()
    RECEIVER.receivePacket(newSocket, filename, fileSize)

def get(udpServer, newSocket, addr, filename):
    if not os.path.isfile(filename):
        # no this file in server
        data = "N"
        fileSize = 0
        data = bytes(data, encoding = 'utf-8') + b'\n' + bytes(str(fileSize), encoding='utf-8')
        udpServer.sendto(data, addr)
        print("Client ask for a not existed file.")
    else:
        data = "Y"
        info = os.lstat(filename)
        fileSize = info.st_size
        data = bytes(data, encoding = 'utf-8') + b'\n' + bytes(str(fileSize), encoding='utf-8')
        udpServer.sendto(data, addr)

        ready, addr = newSocket.recvfrom(1024)
        ready = str(ready, encoding = 'utf-8')
        if (ready == "Y"):
            SENDER = sender.TCPsender()
            SENDER.sendPacket(newSocket, addr, filename, fileSize)


host = '' 
port = 23333 
clientCount = 0
bufsize = 1000
addr = (host, port) 

udpServer = socket(AF_INET,SOCK_DGRAM)
udpServer.bind(addr) 

print("Waiting for command...")
while True:
    request, addr = udpServer.recvfrom(bufsize)
    cmd, flname, fileSize = request.split(b'\n', 2)
    cmd = str(cmd, encoding = 'utf-8')
    flname = str(flname, encoding = 'utf-8')
    fileSize = int(str(fileSize, encoding='utf-8'))
    clientCount += 1
    newSocket = socket(AF_INET,SOCK_DGRAM)
    newAddr = (host, port + clientCount)
    newSocket.bind(newAddr)
    #把新线程的端口告诉客户端
    data = bytes(str(port + clientCount), encoding = 'utf-8')
    udpServer.sendto(data, addr)
    if (cmd == "send"):
        sendThread = threading.Thread(target = send, args = (newSocket, flname, fileSize,))
        sendThread.start()
    else:
        getThread = threading.Thread(target = get, args = (udpServer, newSocket, addr, flname,))
        getThread.start()
    