#! /usr/bin/python
#-*- coding:utf-8 -*-

from struct import *;

fp = open("zuizui.vsq", "rb")

# ヘッダー読み込み
MThd = unpack(">4s", fp.read(4))[0]
headerLen = unpack(">i", fp.read(4))[0]
format = unpack(">h", fp.read(2))[0]
tracks = unpack(">h", fp.read(2))[0]
division = unpack(">h", fp.read(2))[0]

print MThd
print headerLen
print format
print "tracks =", tracks
print division

# マスタートラック読み込み
MTtr = unpack(">4s", fp.read(4))[0]
MTlen = unpack(">i", fp.read(4))[0]
MTdata = fp.read(MTlen)

print MTtr
print MTlen
print MTdata

#一般トラック読み込み
MTtr1 = unpack(">4s", fp.read(4))[0]
MTlen1 = unpack(">i", fp.read(4))[0]

print MTtr1
print MTlen1
"""
query = ">" + str(MTlen1) + "s"
print query
data = unpack(query, fp.read(MTlen1))
for i in data:
"""
    

# 適当に読み込む

deltatime = fp.read(1)
print unpack(">3B6s", fp.read(9))
while True:
    deltatime = fp.read(1)
    ff = fp.read(1)
    type = unpack("B", fp.read(1))[0]
    len = unpack("B", fp.read(1))[0]
    print unpack("127s", fp.read(0x7f))[0]
    if len != 0x7f:
        break

fp.close
