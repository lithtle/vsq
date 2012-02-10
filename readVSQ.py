#! /usr/bin/python
# -*- coding: utf-8 -*-

from struct import *
import sys
import codecs
import re
import pprint
import fcntl

#sys.stdout = codecs.getwriter("shift_jis")(sys.stdout)

__author__ = "lithtle"
__version__ = "0.1.0"

def p(e):
    """要素を綺麗に表示"""
    pp = pprint.PrettyPrinter(indent=4)
    print pp.pprint(e)

def p_str(e):
    """フォーマットした文字列を返す"""
    pp = pprint.PrettyPrinter(indent=4, depth=8)
    return pp.pformat(e)

def readDeltatime(fp):
    """デルタタイム読み込み"""
    ret = 0
    while True:
        i = unpack(">B", fp.read(1))[0]
        if not i & 0x80:
            break
        ret |= 0x7f & i
        ret <<= 7
        ret |= 7
    return ret

class VSQ:
    """vsqファイルのパース"""
    def __init__(self, fp):
        try:
            self.vsq = fp
        except IOError:
            print "invalid filename" >> sys.stderr
        self.parse()
                
    def parse(self):
        """vsqファイルをパース"""
        self.header = self.parseHeader()
        self.masterTrack = self.parseMasterTrack()
        self.generalTracks = self.parseGeneralTracks()

    def unparse(self, fname):
        """vsqファイルをアンパース"""
        if not fname:
            fname = "out.vsq"
        try:
            out = open(fname, "w")
        except IOError:
            print "invalid filename" >> sys.stderr
        header = unparseHeader(self.header)
        masterTrack = unparseMasterTrack(self.masterTrack)
        generalTracks = unparseGeneralTracks(self.generalTracks)
        data = header + masterTrack + generalTracks
        out.write(data)
        out.close()

    def parseHeader(self):
        """ヘッダのパース"""
        header = {
            "MThd": unpack(">4s", self.vsq.read(4))[0],
            "len": unpack(">I", self.vsq.read(4))[0],
            "format": unpack(">H", self.vsq.read(2))[0],
            "tracks": unpack(">H", self.vsq.read(2))[0],
            "division": unpack(">H", self.vsq.read(2))[0]
            }
        return header

    def parseMasterTrack(self):
        """マスタートラックのパース"""
        ret = {
            "MTrk": unpack(">4s", self.vsq.read(4))[0],
            "len": unpack(">i", self.vsq.read(4))[0],
            "data": []
            }

        # 本体部分読み込み
        while True:
            deltatime = readDeltatime(self.vsq)
            tmp = unpack("3B", self.vsq.read(3))
            if tmp[1] == 0x01:
                """text"""
                query = ">" + str(tmp[2]) + "s"
                metaEvent = {
                    "deltatime": deltatime,
                    "type": "\xff\x01",
                    "len": tmp[2],
                    "data": unpack(query, self.vsq.read(tmp[2]))[0]
                    }
                ret["data"].append(metaEvent)
            elif tmp[1] == 0x03:
                """track name"""
                query = ">" + str(tmp[2]) + "s"
                metaEvent = {
                    "deltatime": deltatime,
                    "type": "\xff\x03",
                    "len": tmp[2],
                    "data": unpack(query, self.vsq.read(tmp[2]))[0]
                    }
                ret["data"].append(metaEvent)
            elif tmp[1] == 0x51:
                """tempo"""
                metaEvent = {
                    "deltatime": deltatime,
                    "type": "\xff\x51",
                    "len": 3,
                    "data": unpack(">I", "\x00" + self.vsq.read(3))[0]
                    }
                ret["data"].append(metaEvent)
            elif tmp[1] == 0x58:
                """beat"""
                metaEvent = {
                    "deltatime": deltatime,
                    "type": "\xff\x58",
                    "len": 4,
                    "data": unpack(">4B", self.vsq.read(4))
                }
                ret["data"].append(metaEvent)
            elif tmp[1] == 0x2f:
                """end of track"""
                metaEvent = {
                    "deltatime": deltatime,
                    "type": "\xff\x2f",
                    "len": 0,
                    "data": ""
                }
                ret["data"].append(metaEvent)
                break
        return ret
                    
    def parseGeneralTracks(self):
        """一般トラックのパース"""
        ret = []
        trackLength = self.header["tracks"] - 1 # マスタートラック分減算

        for i in range(trackLength):
            ret.append(Track(self.vsq))
        return ret

    # ここからアンパース関数群
    def unparseHeader(self, header):
        ret = ""
        pass

    def unparseMaster(self, masterTrack):
        pass

    def unparseGeneralTrack(self, generalTracks):
        pass

class Track:
    """一般トラッククラス"""
    def __init__(self, vsq):
        self.data = self.parse(vsq)

    def __str__(self):
        return p_str(self.data)

    def __info__(self):
        p(self.data)
        
    def parse(self, vsq):
        """トラック部分のパース"""
        ret = {
            "MTrk": unpack(">4s", vsq.read(4))[0],
            "len": unpack(">I", vsq.read(4))[0],
            "vocaloidTextData": "",
            "cc": []
            }

        # track name の読み込み
        deltatime = readDeltatime(vsq)
        tmp = unpack("3B", vsq.read(3))
        query = ">" + str(tmp[2]) + "s"
        ret["trackName"] = {
            "deltatime": deltatime,
            "type": "\xff\x03",
            "len": tmp[2],
            "data": unpack(query, vsq.read(tmp[2]))[0]
            }

        # データ部(text, controlchange)の読み込み
        while True:
            deltatime = readDeltatime(vsq)
            tmp = unpack(">3B", vsq.read(3))
            
            if tmp[1] == 0x01:
                """text"""
                query = ">" + str(tmp[2]) + "s"
                ret["vocaloidTextData"] += unpack(query, vsq.read(tmp[2]))[0]
            elif tmp[0] == 0xb0:
                """control change"""
                controlChange = {
                    "deltatime": deltatime,
                    "status": tmp[0],
                    "no": tmp[1],
                    "data": tmp[2]
                    }
                ret["cc"].append(controlChange)
            elif tmp[1] == 0x2f:
                """end of track"""
                ret["endOfTrack"] = {
                    "deltatime": deltatime,
                    "type": "\xff\x2f",
                    "len": 0,
                    "data": ""
                    }
                break
        ret["vocaloidTextData"] = self.parseString(ret["vocaloidTextData"])
        return ret
                
    def parseString(self, dataStr):
        """引数の dataStr(vsqのテキスト部分) をパース"""
        ret = {
            "Common": {},
            "Master": {},
            "Mixer": {},
            "EventList": [],
            "HandleList": [],
            "BPList": {}
            }
        section = ""

        d = re.compile("DM:\d{4}:").sub("", dataStr).split("\n")
        d.pop()                 # 最後の改行要素を削除

        for i in d:
            if re.compile("\[.+\]").match(i):
                # [hoge] から section name の取り出し
                section = i[1:-1]
                continue

            # section の内部
            key, value = i.split("=")
            if re.compile("Common|Master|Mixer").match(section):
                ret[section][key] = value
            elif section == "EventList":
                ret["EventList"].append(Event(key, value))
            elif re.compile("ID#\d+").match(section):
                eventNumber = int(section[3:]) # ID#0001 から ID番号を得る
                ret["EventList"][eventNumber].set(key, value)
            elif re.compile("h#\d+").match(section):
                handleNumber = int(section[2:])

                # ret["HandleList"][handleNumber]が存在するかどうか
                # なければ配列に append する
                if not ret["HandleList"][handleNumber:handleNumber+1]:
                    ret["HandleList"].append(Handle(section))
                ret["HandleList"][handleNumber].set(key, value)
            elif re.compile(".+BPList").match(section):
                if not section in ret["BPList"]:
                    ret["BPList"].update({section: {}})
                ret["BPList"][section][key] = value
                
        return ret


class Event:
    """ID#で始まるイベントを格納する"""
    def __init__(self, time=None, id=None):
        self.id = id
        self.data = {
            id: time
            }

    def __str__(self):
        return p_str(self.data)

    def info(self):
        """情報の表示"""
        p(self.data)

    def set(self, k, v):
        """インスタンス変数 data に値をセット """
        self.data.update({k: v})
        

class Handle:
    """h#ではじまるハンドルイベントクラス"""
    def __init__(self, id=None):
        self.id = id
        self.data = {}

    def __str__(self):
        return p_str(self.data)

    def info(self):
        """情報の表示"""
        p(self.data)

    def set(self, k, v):
        self.data.update({k: v})


def edit(fp):
    """vsqファイルをいろいろいじる関数

    今回はさ行の要素{/さ/, /し/, ... /しょ/}の前に
    /s/ ノート{len: 120}を追加してみる
    くっそコードになりそうな感じ
    """
    vsq = VSQ(fp)
    txt = vsq.generalTracks[0].data["vocaloidTextData"]
    eventlist = txt["EventList"]
    handlelist = txt["HandleList"]
    target_handle = []
    target_event = []

    # さ行に該当するハンドルとそのハンドルを参照しているイベントを得る
    for i in range(len(handlelist)):
        # 歌詞イベントでなければループを続行
        if not handlelist[i].data.has_key("L0"):
            continue

        L0 = handlelist[i].data["L0"].split(",")

        if re.compile("[sS]\s[aiMeo]").match(L0[1][1:-1]): # match "s a" => s a
            id = handlelist[i].id
            target_handle.append(i)
            for j in range(len(eventlist)):
                if not eventlist[j].data.has_key("LyricHandle"):
                    continue
                if not eventlist[j].data["LyricHandle"] == id:
                    continue
                target_event.append(j)

    # 新しい歌詞イベントの追加
    for i in range(len(target_handle)):
        j = target_handle[i]
        k = target_event[i]
        newID = "h#%04d" % j
        eventID = "ID#%04d" % k
        newLyric = Handle()
        newLyric.data = {"L0": '"s","s",0.000000,64,1'}
        newEvent = Event()
        newEvent.data = {
            "PMBendDepth": "8",
            "PMBendLength": "14",
            "PMbPortamentoUse": "0",
            "DEMdecGainRate": "50",
            "LyricHandle": "",
            "Type": "Anote",
            "Length": "",
            "DEMaccent": "50",
            "Dynamics": "64"
            }

        prev = eventlist[k-1]
        current = eventlist[k]
        diff = int(current.data[current.id]) - (int(prev.data[prev.id]) + int(prev.data["Length"]))

        if diff == 0 and int(prev.data["Length"]) < 120:
            return 1
        elif 0 < diff < 120:
            newEvent.data["Length"] = str(diff)
            newEvent.data[eventID] = str(int(eventlist[k].data[eventID]) - diff)
        else:
            newEvent.data["Length"] = str(120)
            newEvent.data[eventID] = str(int(eventlist[k].data[eventID]) - 120)
        newEvent.data["LyricHandle"] = newID

        # j 以降の[h#....]のインクリメント
        for l in range(j, len(handlelist), 1):
            handlelist[l].id = "h#%04d" % (int(handlelist[l].id[2:]) + 1)
        # k 以降の[ID#....]のインクリメント
        for l in range(k, len(eventlist), 1):
            if eventlist[l].id == "EOS":
                continue
            time = eventlist[l].data[eventlist[l].id]
            del eventlist[l].data[eventlist[l].id]
            eventlist[l].id = "ID#%04d" % (int(eventlist[l].id[3:]) + 1)
            eventlist[l].data[eventlist[l].id] = time
            if eventlist[l].data.has_key("LyricHandle"):
                eventlist[l].data["LyricHandle"] = "h#%04d" % (int(eventlist[l].data["LyricHandle"][2:]) + 1)
            if eventlist[l].data.has_key("VibratoHandle"):
                eventlist[l].data["VibratoHandle"] = "h#%04d" % (int(eventlist[l].data["VibratoHandle"][2:]) + 1)

        handlelist.insert(j, newLyric)
        eventlist.insert(k, newEvent)
        for l in range(len(target_handle)):
            target_handle[l] += 1
            target_event[l] += 1
            

    for i in eventlist:
        print i
    print "---------------------"
    for j in handlelist:
        print j

    
def main():
    if not len(sys.argv) == 2:
        print "invalid argument" >> sys.stderr
        print "usage: %s [self.vsqfile]" % argv[0] >> sys.stderr
        exit(1)

    fp = open(sys.argv[1], "rb")
    fcntl.flock(fp, fcntl.LOCK_EX)
    edit(fp)
    fcntl.flock(fp, fcntl.LOCK_UN)
    fp.close()

if __name__ == "__main__":
    main()


    
