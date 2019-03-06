from socket import *
import threading
import struct
import os
import stat
import time
import random

import headerHelper

class TCPreceiver():
    def __init__(self):
        self.receiveBuffer = []
        self.receiveBufferSize = 20
        self.mutex = threading.Lock()
        self.fileIter = 0
        self.waitingTime = 0.0000001
        self.finish = False
        self.addrTemp = (0, 0)
        
    def receivePacket(self, receiveSocket, fileName, fileSize):
        self.fileSize = fileSize
        ACK = 0
        bufsize = 1024
        print("Now begin to receive the file.")
        print ("FileName is %s, fileSize is %d" %(fileName, fileSize))
        receiveSocket.settimeout(4)
        timeoutCount = 0

        writeFile = threading.Thread(target = self.writeFile, args = (fileName,))
        writeFile.start()

        
        while(True):
            if timeoutCount >= 10:
                break
            if (self.fileIter + 1 == fileSize):
                if self.finish:
                    break
                time.sleep(self.waitingTime)
                continue
            # 接收缓存使用量 小于 接收缓存大小（单位：分组）
            if len(self.receiveBuffer) < self.receiveBufferSize:
                try:
                    data, addr = receiveSocket.recvfrom(bufsize)
                    self.addrTemp = addr
                except BaseException as e:
                    print (e)
                    print("Receive packet timeout happends.")
                    timeoutCount = timeoutCount + 1
                    time.sleep(self.waitingTime)
                else:
                    
                    #header长度8个字节
                    header = data[0:8]
                    data = data[8:]
                    seqnum, flIter = struct.unpack("II", header)
                    print("Received packet " + str(seqnum))

                    #如果是期望收到的packet，则写入缓存
                    if (seqnum == ACK):
                        self.fileIter = flIter
                        print("Packet accepted, ACK: " + str(ACK))
                        self.mutex.acquire()
                        self.receiveBuffer.append(data)
                        self.mutex.release()

                        rwnd = self.receiveBufferSize - len(self.receiveBuffer)
                        # print("rwmd: " + str(rwnd))
                        feedback = struct.pack("II", ACK, rwnd)
                        receiveSocket.sendto(feedback, addr)
                        ACK += 1
                    else:
                        # print("Packet not accepted, ACK: " + str(ACK))
                        rwnd = self.receiveBufferSize - len(self.receiveBuffer)
                        if ACK == 0:
                            continue
                        feedback = struct.pack("II", ACK-1, rwnd)
                        receiveSocket.sendto(feedback, addr)
            # 接收窗口已满
            else:
                while len(self.receiveBuffer) >= self.receiveBufferSize:
                    # 发送拒收信息
                    # print("window is full, rwnd = 0 " + str(ACK))
                    rwnd = 0
                    if ACK == 0:
                        continue
                    feedback = struct.pack("II", ACK-1, rwnd)
                    receiveSocket.sendto(feedback, self.addrTemp)
                    time.sleep(self.waitingTime)

                # 接收窗口重新有空余，发送接收信息
                rwnd = self.receiveBufferSize - len(self.receiveBuffer)
                if ACK == 0:
                    continue
                feedback = struct.pack("II", ACK-1, rwnd)
                receiveSocket.sendto(feedback, self.addrTemp)
                

                
        print("---------------")
        if (timeoutCount >= 10):
            print("Too long not receive packet, server close.")
        else:
            print("Receive file successfully.")
                

    def writeFile(self, fileName):
        #创建文件
        with open(fileName, "ab") as file:
            i = 0
            while True:
                if len(self.receiveBuffer) != 0:
                    file.write(self.receiveBuffer[0])
                    # print("Write " + str(i) + " packet.")
                    i += 1
                    self.mutex.acquire()
                    self.receiveBuffer.pop(0)
                    if self.fileIter + 1 == self.fileSize and len(self.receiveBuffer) == 0:
                        self.finish = True
                        self.mutex.release()
                        break
                    self.mutex.release()
                else:
                    time.sleep(self.waitingTime)
        file.close()