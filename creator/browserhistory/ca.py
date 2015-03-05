#!/usr/bin/python

import os
import struct
import math
import datetime

class CacheFile(object):
    def __init__(self, path):
        self.fname = path
        #print self.fname
        try:
            cf = open(self.fname, "r")
            buf = cf.read()
        except:
            print ("Cannot read %s" % self.fname)
            raise
        self.dlength = struct.unpack(">I", buf[-4:])[0]
        mdstart =  self.dlength
        xyzzy = int(math.ceil(float(self.dlength) / 262144))*2+4
        mdstart += xyzzy
        self.version, self.fetchcount,self.lfd1raw, self.lfd2raw, self.frequency, self.expdateraw, self.keylength  = struct.unpack(">IIIIIII", buf[mdstart:mdstart+28])

        self.lfd1 = datetime.datetime.fromtimestamp(self.lfd1raw)
        self.lfd2 = datetime.datetime.fromtimestamp(self.lfd2raw)
        self.expdate = datetime.datetime.fromtimestamp(self.expdateraw)

        urlstart = mdstart + 29
        t = buf[urlstart:].index("\000")
        print xyzzy,buf[urlstart:urlstart+t]

try:

    cdir = "/home/visti/.cache/mozilla/firefox/z3g0sa88.default/cache2/entries"
    cfiles = os.listdir(cdir)
except:
    print("poskelleen meni")


clist = []

for d in cfiles:
    try:
        r = CacheFile(cdir+"/"+d)
        clist.append(r)
    except:
        pass
            



