from socket import *
import threading
import struct
import os
import stat
import time


import headerHelper

class TCPsender():
    def __init__(self):
        self.bufsize = 1024
        self.fSize = 800
        self.newSeqnum = 0
        self.fileIter = 0
        self.finish = False
        self.windowSize = 20
        self.rwnd = 20
        self.cwnd = 1
        self.state = 0 # 0 为慢启动，1 为快速恢复
        self.ssthresh = float('inf') #ssthresh 初始化无穷大
        self.sendList = []
        self.base = 0
        self.waitingTime = 0.0000001
        self.seqInPacket = 0
        self.mutex = threading.Lock()

    def sendPacket(self, senderSocket, dst, filePath, fileSize):

        #socket设置超时限制
        senderSocket.settimeout(4)

        #启动getACK线程
        getACKFunc = threading.Thread(target = self.getACK, args = (senderSocket, fileSize,))
        readFile = threading.Thread(target = self.readFile, args = (filePath, fileSize,))
        getACKFunc.start()
        readFile.start()
        
        #开始传输文件
        while (not self.finish):
            self.mutex.acquire()
            # LastPacketSent - LastPacketAcked <= min {rwnd, cwnd}
            if self.newSeqnum - self.base + 1 > self.rwnd or self.newSeqnum - self.base + 1 > self.cwnd:
                self.mutex.release()
                continue
            # 发送窗口有等待发送的packet
            if len(self.sendList) != 0 and self.newSeqnum - self.base < len(self.sendList):
                # 获得窗口队列可发送而未发送的packet
                packet = self.sendList[self.newSeqnum - self.base]
                # 发送packet
                # print ("Sending packet " + str(self.newSeqnum))
                senderSocket.sendto(packet, dst)
                self.newSeqnum = self.newSeqnum + 1
                print("base:" + str(self.base) + " seq:" + str(self.newSeqnum) + " len:" + str(len(self.sendList)))
                print("cwnd:" + str(self.cwnd))
            self.mutex.release()
            #控制发送间隔
            time.sleep(self.waitingTime)
            
        #文件传输结束
        print("Finish sending the file.")
        senderSocket.close()

    def readFile(self, filePath, fileSize):
        print ("Now begin to send the file.")
        print ("filePath is %s, fileSize is %d" %(filePath, fileSize))
        with open(filePath, 'rb') as file:
            info = os.lstat(filePath)
            fileSize = info.st_size
            stream = file.read()
            #开始传输文件
            while True:
                self.mutex.acquire()
                if len(self.sendList) < self.windowSize:
                    packet = b''
                    for i in range(self.fileIter, self.fileIter + self.fSize):
                        if (i == fileSize):
                            break
                        packet = packet + bytes((stream[i],))
                        self.fileIter = self.fileIter + 1
                    if (packet != b''):
                        #packet添加header
                        header = headerHelper.getHeader(self.seqInPacket, self.fileIter - 1)                            
                        packet = struct.pack("II", header["seqnum"], header["fileIter"]) + packet
                        self.sendList.append(packet) #将报文添加进发送窗口
                        self.seqInPacket += 1
                        # print("appending packet")
                        # print("base:" + str(self.base) + " seq:" + str(self.newSeqnum) + " len:" + str(len(self.sendList)))
                        i += 1
                    else:
                        self.mutex.release()
                        break
                    self.mutex.release()
                else:
                    # 发送窗口已满
                    self.mutex.release()
                    time.sleep(self.waitingTime)
            
            print("READFILE completed.")
        file.close()


    def getACK(self, senderSocket, fileSize):
        # 发送窗口有等待确认的序号
        seqTemp = 0
        overtime = 0 # 同一序列seqTemp报文重发次数
        redundancyACK = 0 # 冗余ACK
        redundancyTimes = 0 # 冗余次数
        while True:
            if (self.newSeqnum - self.base) != 0:
                try:
                    header, addr = senderSocket.recvfrom(self.bufsize)
                except BaseException as e:
                    #超时
                    print(e)
                    print("Receive ACK timeout happends.")
                    #超时时发送方将重传所有已发送而未确认的分组
                    if (self.mutex.acquire(5)):
                        if seqTemp == self.base:
                            overtime += 1
                        else:
                            seqTemp = self.base
                            overtime = 1
                        # 重设指针和Seq
                        self.ssthresh = self.cwnd // 2 
                        self.cwnd = 1 # 慢启动
                        self.newSeqnum = self.base
                        self.mutex.release()

                else:
                    #没超时
                    if (self.mutex.acquire(5)):
                        ACK, rwnd = struct.unpack("II", header)
                        # 假如收到的是发送窗的base分组，则更新窗口队列
                        if (ACK == self.base):
                            redundancyTimes = 0
                            print("Receive ACK " + str(ACK))
                            self.base += 1
                            self.sendList.pop(0)  # 更新窗口队列，将base分组弹出
                            # print("base:" + str(self.base) + " seq:" + str(self.newSeqnum) + " len:" + str(len(self.sendList)))
                            if self.cwnd < self.ssthresh:
                                self.cwnd *= 2 #慢启动
                            else:
                                self.cwnd += 1 #快速恢复

                            #接收到全部的ACK
                            if (self.fileIter == fileSize and len(self.sendList) == 0):
                                self.finish = True
                                self.mutex.release()
                                break
                        else:
                            #未按序接收确认时发送方将重传所有已发送而未确认的分组
                            print("[fault]Receive ACK " + str(ACK))
                            self.newSeqnum = self.base
                            if ACK == redundancyACK:
                                redundancyTimes += 1
                            else:
                                redundancyACK = ACK
                            if redundancyTimes >= 3:
                                self.ssthresh = self.cwnd // 2
                                self.cwnd = self.ssthresh + 3
                        self.rwnd = rwnd
                        self.mutex.release()
            
            if overtime >= 10:
                break
        #接收ACK超时过多的情况处理，关闭文件发送
        print("---------------")
        print("Finish receiving ACK.")
        if (not self.finish):
            print ("Too much receive ACK timeout happends, maybe server has been closed.")
            self.finish = True