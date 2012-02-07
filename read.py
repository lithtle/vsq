#! /usr/bin/python
# -*- coding: utf-8 -*-

from struct import *
import re
import pprint

def readDeltatime(fp):
    ret = 0
    while True:
        i = unpack(">B", fp.read(1))[0]
        if not (i & 0x80):
            break
        ret |= 0x7f & i
        ret <<= 7
    ret |= i
    return ret

def parse():
    ret = []
    fp = open("zuizui.vsq", "rb")
    data = ""

    # ヘッダ読み込み
    header = {
        "MThd": unpack(">4s", fp.read(4))[0],
        "header_length": unpack(">i", fp.read(4))[0]
        "format": unpack(">h", fp.read(2))[0]
        "tracks": unpack(">h", fp.read(2))[0]
        "division": unpack(">h", fp.read(2))[0]
        }

    for i in range(header["tracks"]):
        mttr = fp.read(4)
        length = unpack(">i", fp.read(4))[0]
        
        data += "track_num=" + str(i) + "\n"
        data += "track_len=" + str(length) + "\n"
        
        while True:
            deltatime = readDeltatime(fp)
            c = unpack("B", fp.read(1))[0]
            
            if c == 0xff:
                type = unpack("B", fp.read(1))[0]
                
                if type == 0x01:
                    """text"""
                    size = unpack("B", fp.read(1))[0]
                    text = fp.read(size)
                    data += text
                    continue
                elif type == 0x03:
                    """track name"""
                    size = unpack("B", fp.read(1))[0]
                    track_name = fp.read(size)
                    data += "track_name=" + track_name + "\n"
                    continue
                elif type == 0x51:
                    """set tempo"""
                    size = unpack("B", fp.read(1))[0]
                    tempo = unpack(">i", fp.read(4))[0]
                    data += "tempo=" + str(tempo) + "\n"
                    continue
                elif type == 0x58:
                    """beat"""
                    size = unpack("B", fp.read(1))[0]
                    beat = unpack(">i", fp.read(4))[0]
                    data += "beat=" + str(beat) + "\n"
                    continue
                elif type == 0x2f:
                    """end of track"""
                    readDeltatime(fp)
                    break
            elif type == 0xb0:
                """control change"""
                data += unpack("2s", fp.read(2))[0]
                continue
    fp.close()
    p = re.compile("DM:\d{4}:")
    data = p.sub("", data)
    return {
        "data": data.split("\n"),
        "tracks": tracks,
        "tempo": tempo,
        "division": division
        }

def get_tracks(data):
    ret = {}
    k = []
    p = re.compile("track_num.*")
    for i in range(0, len(data), 1):
        if p.match(data[i]):
            k.append(i)

    for i in range(0, len(k), 1):
        if i == len(k) - 1:
            ret.update({i: data[k[i]:]})
        else:
            ret.update({i: data[k[i]:k[i+1]]})
    return ret

class VSQ:
    def __init__(self, t):
        self.track = []
        self.set_tracks(t)

    def set_tracks(self, t):
        for i in range(len(t)):
            j = Track(t[i])
            self.track.append(j)

class Track:
    def __init__(self, a_track):
        self.data = []
        self.bplist = []
        self.parse(a_track)
        self.set_event()
        print self.data

    def parse(self, a_track):
        for i in a_track:
            a_event = i.split("=")
            if len(a_event) == 1:
                a_event.append("")
            self.data.append(tuple(a_event))
        
    def set_event(self):
        id = re.compile("ID#\d{4}")
        print self.data
        for i in range(len(self.data)):
            refferd_key = self.data[i][0]
            refferd_value = self.data[i][1]
            if not id.match(refferd_value):
                continue

            for j in range(len(self.data)):
                target = re.compile("\["+refferd_value+"\]")
                key = self.data[j][0]
                value = self.data[j][1]
                if not target.match(key):
                    continue
                e = Event()
                e.setID(refferd_key)
                for k in range(j+1, len(self.data), 1):
                    if re.compile("\[ID#\d{4}\]").match(self.data[k][0]):
                       break 
                    e.update_event(self.data[k][0], self.data[k][1])
                del self.data[j:k]
                self.data[i] = (self.data[i][0], e)
                break
            
                
    def __str__(self):
        return pp_str(self.events)

class Event:
    def __init__(self):
        self.events = {}
    def setID(self, str):
        self.ID = str
    def getID(self):
        return self.ID
    def update_event(self, key, value):
        self.events.update({key: value})
    def __str__(self):
        return "class::" + self.ID

            
if __name__ == "__main__":
    info = parse()
    data = info["data"]

    tracks = get_tracks(data)
    """
    print len(tracks)
    print tracks[0]
    print tracks[1]
    """
    vsq = VSQ(tracks)
    
