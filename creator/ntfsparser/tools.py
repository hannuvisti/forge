'''
Created on 22 May 2013

@author: visti
Copyright 2013 Hannu Visti

This file is part of ForGe forensic test image generator.
ForGe is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ForGe.  If not, see <http://www.gnu.org/licenses/>.

'''

import struct
import binascii
import time
import datetime


def _Split_String(s):
    __i=0
    while __i < len(s):
        __i += 2
        yield s[__i-2:__i]
        

def _hexdump(data,highlight=-1,endlight=-1):
    i = 0
    while i < len(data):
        dhex = binascii.b2a_hex(data[i:i+16])
        ascstring = ""
        print "%04X" % i,
        for r in _Split_String(dhex):
            if highlight <= i <= endlight:
                print r,
                #print '\033[1m'+__r+'\033[0m',
            else:
                print r,
            if int(r,16) >= 32 and int (r,16) <= 127:
                ascstring += chr(int(r,16))
            else:
                ascstring += '.'
        
        print ((32-len(dhex))/2)*"   ",
        #print 'X'*((32-len(dhex))*2),
        print " |  ",ascstring
        
        
        i += 16
    print "--"

def _Unpack48(bbuf):
    """ perform struct.unpack to six bytes - needed to unparse parent dir references in filenames """
    
    if len(bbuf) != 6:
        print "unable to unpack", bbuf
        exit(1)
    byte_tmp = ""
    for i in range(5,-1,-1):
        byte_tmp += '%02x' % struct.unpack("B",bbuf[i])[0]

    return int(byte_tmp,16)

def _Pack48(data):
    buf = ""
    for i in range(0,48,8):
        c = data
        mask = (2 ** (i+8)) -1
        buf += struct.pack("B",(c & mask) >>i)
    return buf

    
        
class _NTFSTime:
    """ Change NTFS time attribute to unix time. NTFS time is the amount of 100 nanosecond intervals since 1/1/1601  
    
    def __init__(self, tt=None):
        if tt == None:
            self.tt_time = self.tt_sec = self.tt_nsec = 0
            return
        diff = (369*365+89)*24*3600*10000000
        self.tt_time = tt
        self.tt_sec = long ((self.tt_time - diff)/10000000)
        self.tt_nsec = ((self.tt_time-diff) - self.tt_sec*10000000)*100
        
    def printtime(self):
        print time.localtime(self.tt_sec), self.tt_nsec"""
        
    def __init__(self,buf=None):
        if not buf:
            return None
        if len(buf) != 32:
            return None
        """
        self.a_ctime = _NTFSTime(struct.unpack("<Q", self.a_content.read_data(0,8))[0])       # creation
        self.a_atime = _NTFSTime(struct.unpack("<Q", self.a_content.read_data(8,16))[0])      # alteration
        self.a_mtime = _NTFSTime(struct.unpack("<Q", self.a_content.read_data(16,24))[0])     # MFT change
        self.a_rtime = _NTFSTime(struct.unpack("<Q", self.a_content.read_data(24,32))[0])     # File read time"""
        
        """ MACE timestamp extraction
        NTFS has timestamps in order creation, modification, entry changed, access 
        """
        
        self.raw_ctime,self.raw_mtime,self.raw_etime,self.raw_atime=struct.unpack("<QQQQ", buf)
        diff = (369*365+89)*24*3600*10000000
        
        self.ctime_sec = long((self.raw_ctime-diff)/10000000)
        self.ctime_nsec = ((self.raw_ctime-diff) -self.ctime_sec*10000000)*100
        self.ctime = datetime.datetime.fromtimestamp(self.ctime_sec)
        
        self.atime_sec = long((self.raw_atime-diff)/10000000)
        self.atime_nsec = ((self.raw_atime-diff) -self.atime_sec*10000000)*100
        self.atime = datetime.datetime.fromtimestamp(self.atime_sec)
                
        self.mtime_sec = long((self.raw_mtime-diff)/10000000)
        self.mtime_nsec = ((self.raw_mtime-diff) -self.mtime_sec*10000000)*100
        self.mtime = datetime.datetime.fromtimestamp(self.mtime_sec)
                
        self.etime_sec = long((self.raw_etime-diff)/10000000)
        self.etime_nsec = ((self.raw_etime-diff) -self.etime_sec*10000000)*100
        self.etime = datetime.datetime.fromtimestamp(self.etime_sec)
    def raw_time(self):
        buf = struct.pack("<QQQQ",self.raw_ctime,self.raw_mtime,self.raw_etime,self.raw_atime)
        return buf
    def change_ctime(self,lt):
        diff = (369*365+89)*24*3600*10000000
        ts = time.mktime(lt.timetuple())
        self.ctime_sec = long(ts)
        self.raw_ctime = 10000000*self.ctime_sec + diff
        self.ctime = datetime.datetime.fromtimestamp(self.ctime_sec)
    def change_atime(self,lt):
        diff = (369*365+89)*24*3600*10000000
        ts = time.mktime(lt.timetuple())
        self.atime_sec = long(ts)
        self.raw_atime = 10000000*self.atime_sec + diff
        self.atime = datetime.datetime.fromtimestamp(self.atime_sec)   
    def change_mtime(self,lt):
        diff = (369*365+89)*24*3600*10000000
        ts = time.mktime(lt.timetuple())
        self.mtime_sec = long(ts)
        self.raw_mtime = 10000000*self.mtime_sec + diff
        self.mtime = datetime.datetime.fromtimestamp(self.mtime_sec)
    def change_etime(self,lt):
        diff = (369*365+89)*24*3600*10000000
        ts = time.mktime(lt.timetuple())
        self.etime_sec = long(ts)
        self.raw_etime = 10000000*self.etime_sec + diff
        self.etime = datetime.datetime.fromtimestamp(self.etime_sec)
        
    def change_all_times(self,lt):
        self.change_atime(lt)
        self.change_mtime(lt)
        self.change_etime(lt)
        self.change_ctime(lt)
                
    def printtime(self):
        print "Ctime:", self.ctime
        print "Atime:", self.atime
        print "Mtime:", self.mtime
        print "Etime:", self.etime
        
        
        
