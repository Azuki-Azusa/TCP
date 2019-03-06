import struct

def getHeader(seqnum, fileIter):
  header = {
    "seqnum" : seqnum,
    "fileIter" : fileIter #packet末端在文件中的位置
  }
  return header

'''
------struct和字典的配合使用样例---------
header = getHeader(False, 1)
#  ? -> 布尔型  I -> 整型
temp = struct.pack("?I", header["ACK"], header["seqnum"])
ACK, seqnum = struct.unpack("?I", temp)
print (ACK)
print (seqnum)

输出结果：
False
1
'''