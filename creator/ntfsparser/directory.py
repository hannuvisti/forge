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
from tools import _Unpack48
from tools import  _hexdump
from tools import _NTFSTime
import sys



    


def _ParseIndexEntries(block):
    """ iterator - returns a DirIndexEntry block until no more are available
    in which case the iterator exhausts """
    
    pq = 0
    pflags = 0
    while (pflags & 2) == 0:
        pflags, = struct.unpack("<I", block[pq+12:pq+16])
        """        if __pflags & 2 != 0:
            if __pflags & 1 != 0:
                print "FOOOOO"
            return"""
            
        l, = struct.unpack("<H", block[pq+8:pq+10])
        tmp = pq
        pq += l
        
        
        yield [block[tmp:pq],tmp]
        
class _DirIndexEntry:
    def __init__(self, p,location):
        self.parent = p
        self.filerecord = 0
        self.parentdir = 0
        self.parentdirseq = 0
        self.flags = 0
        self.location=location
        
    def init_entry(self, block, kind):
        self.filerecord = _Unpack48(block[0:6])
        self.seqnumber, = struct.unpack("<H", block[6:8]) 
        self.elength,self.alength = struct.unpack("<HH", block[8:12])
        self.flags, = struct.unpack("<I", block[12:16])
        if self.flags & 1:
            self.vcn, = struct.unpack("<Q", block[-8:])
        else:
            self.vcn = -1
       
        self.filename = ""
        
        if kind == 0x30 and (self.flags & 2) == 0:
            self.parentdir = _Unpack48(block[0x10:0x16])
            self.parentdirseq, = struct.unpack("<H", block[0x16:0x18])
            """
            self.ctime = _NTFSTime(struct.unpack("<Q", block[0x18:0x20])[0])
            self.atime = _NTFSTime(struct.unpack("<Q", block[0x20:0x28])[0])
            self.mtime = _NTFSTime(struct.unpack("<Q", block[0x28:0x30])[0])
            self.rtime = _NTFSTime(struct.unpack("<Q", block[0x30:0x38])[0])
            """
            self.time = _NTFSTime(block[0x18:0x38])
  
            
            self.fnamelength, = struct.unpack("B", block[0x50])
            unicodename = block[0x52:0x52+self.fnamelength*2]
            try:
                self.filename = unicodename.decode("utf-16-le")
            except:
                print "decode error", unicodename
                self.filename = ""

            
                                        

        
    def print_entry(self):
        if not self.flags & 2:
            print self.filename, self.filerecord, self.parent.parent.parent.f_mft[self.parentdir].getFileName()
        return
    
        print "File reference:",self.filerecord, "/", self.seqnumber
        print "Parent dir:", self.parentdir, "/", self.parentdirseq
        print "Flags:", self.flags
        print "Elen,Alen:", self.elength, self.alength
        print "Vcn:", self.vcn
        print "Name:", self.filename
        if self.flags & 2:
            return
        print "Times:", self.time
        print "---"
        
        
