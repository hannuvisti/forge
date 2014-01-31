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
from attributes import parse_attributes
from attributes import _NTFSAttributeData, _NTFSAttributeStandard, _NTFSAttributeFileName
from attributes import NTFS_ATTRIBUTES
from itertools import chain
from ui.uitools import ForensicError
import sys

class _MftEntry:
    def __init__(self, mft,parent,location):
        self.m_updateoffset = struct.unpack("<H", mft[4:6])[0]
        self.m_fixup = struct.unpack("<H", mft[6:8])[0]
        self.m_logsequence = struct.unpack("<Q", mft[8:16])[0]
        self.m_sequence = struct.unpack("<H", mft[16:18])[0]
        self.m_hardlink = struct.unpack("<H", mft[18:20])[0]
        self.m_attroffset = struct.unpack("<H", mft[20:22])[0]
        self.m_flags = struct.unpack("<H", mft[22:24])[0]
        self.m_size = struct.unpack("<I", mft[24:28])[0]
        self.m_allocated = struct.unpack("<I", mft[28:32])[0]
        self.m_filereference = struct.unpack("<Q", mft[32:40])[0]
        self.m_nextattribute = struct.unpack("<H", mft[40:42])[0]
        self.m_mftnumber = struct.unpack("<I", mft[44:48])[0]
        self.m_attributes = []
        self.m_data = []
        self.m_qdata = {}
        self.parent = parent
        self.m_dirTree = []
        self.m_dirtmp = []
        self.m_ir_entry = []
        self.m_parentdir = None
        self.m_location = location


        """ Fixup array """

        x = self.m_updateoffset + 2
        y = self.m_fixup - 1
        mtmp = mft
        for z in range (0,y):
            
            f = mft[x] + mft[x+1]
            x += 2
            mtmp = mtmp[:z*512+510]+f+mtmp[(z+1)*512:]
        if self.m_attroffset != 0:
            agen = parse_attributes(mtmp[self.m_attroffset:self.m_size+1])
            o = self.m_attroffset
            for t in agen:
                attr = NTFS_ATTRIBUTES[t[2]](self)
                """" generator returns [start position, length, attribute id] """
                attr.init_attribute(mtmp[t[0]+o:t[0]+t[1]+1+o],self.m_location+t[0]+o)

                self.m_attributes.append(attr)
                if isinstance(attr, _NTFSAttributeData) == True:
                    
                    data_entry = [attr.a_name, attr.a_content]
                    self.m_data.append(data_entry)
                    self.m_qdata[attr.a_name] = attr.a_content
                if isinstance(attr, _NTFSAttributeFileName) == True:
                    self.set_parent_dir(attr.a_parentdir)
                    
        #print self.m_mftnumber, self.m_flags, self.get_file_name()   
            
    def get_data_keys(self):
        for key in self.m_qdata.keys():
            print key
            
    def get_slack(self):
        slack = []
       
        for qkey in self.m_qdata.keys():         
            attr = self.m_qdata[qkey]
            s = attr.get_slack()
            if s:
                slack.append(attr.get_slack())

        return slack if len(slack) > 0 else None
    
    """ This is one of the key functions """
    def write_data(self):
        for f in self.m_attributes:
            f.write_attribute()
    """ This is one of the key functions 
    Implement a MACE time change algorithm
    Expect a named list of form
    btime["ctime"] = datetime()
    or
    btime["all"] = datetime() which will set default.
    if all and individual times present, individual attributes take precedence """
    
    
    def change_std_time(self,btime):
        mtime=atime=ctime=etime=None
        try:
            mtime=atime=ctime=etime = btime["all"]
        except KeyError:
            pass
        try:
            mtime = btime["mtime"]
        except KeyError:
            pass
        try:
            atime = btime["atime"]
        except KeyError:
            pass
        try:
            ctime = btime["ctime"]
        except KeyError:
            pass
        try:
            etime = btime["etime"]
        except KeyError:
            pass        
        for f in self.m_attributes:
            if isinstance(f, _NTFSAttributeStandard):
                if mtime:
                    f.a_time.change_mtime(mtime)
                if atime:
                    f.a_time.change_atime(atime)
                if ctime:
                    f.a_time.change_ctime(ctime)
                if etime:
                    f.a_time.change_etime(etime)
                f.write_attribute()
            
    def change_fname_time(self,btime):
        mtime=atime=ctime=etime=None
        try:
            mtime=atime=ctime=etime = btime["all"]
        except KeyError:
            pass
        try:
            mtime = btime["mtime"]
        except KeyError:
            pass
        try:
            atime = btime["atime"]
        except KeyError:
            pass
        try:
            ctime = btime["ctime"]
        except KeyError:
            pass
        try:
            etime = btime["etime"]
        except KeyError:
            pass        
        for f in self.m_attributes:
            if isinstance(f, _NTFSAttributeFileName):
                if mtime:
                    f.a_time.change_mtime(mtime)
                if atime:
                    f.a_time.change_atime(atime)
                if ctime:
                    f.a_time.change_ctime(ctime)
                if etime:
                    f.a_time.change_etime(etime)
                f.write_attribute()
    def query_std_time(self):
        for f in self.m_attributes:
            if isinstance(f,_NTFSAttributeStandard):
                return f.a_time
        raise ForensicError("Standard time attribute not found")
    def query_fname_time(self):
        for f in self.m_attributes:
            if isinstance(f,_NTFSAttributeFileName):
                return f.a_time
        raise ForensicError("Filename time attribute not found")
            
                    
     
    def mft_data(self, name, offset, dlength):
        result = ""
        attr = self.m_qdata[name]
        result = attr.read_data(offset, dlength)
        return result
    
    def locate_data(self,name,offset):
        attr = self.m_qdata[name]
        return attr.locate_data(offset)
  

    def return_unnamed_data(self):
        try:
            return self.m_qdata[None]
        except KeyError:
            raise ForensicError("Cannot locate unnamed data attribute");

    def get_directory_structure(self):
        if self.m_flags & 3 != 3:
            return;
        for ddir in self.m_dirTree:
            ddir.print_entry()
                
    def set_directory(self):
        self.m_dirTree = self.m_ir_entry
        
    def set_parent_dir(self,pdir):
        self.m_parentdir = pdir
        
    
    def get_file_name(self):
        for a in self.m_attributes:
            if a.a_type == 0x30:
                return a.a_ascname
        return ""
        
    def mft_display(self):
        print "Filename:", self.get_file_name()
        print "Offset to update sequence:", self.m_updateoffset 
        print "Number of entries in fixup array:", self.m_fixup 
        print "Logfile sequence number:", self.m_logsequence 
        print "Sequence number:", self.m_sequence
        print "Hard link count", self.m_hardlink
        print "Offset to first attribute:", self.m_attroffset
        print "Flags:", self.m_flags
        print "Used size of MFT entry:", self.m_size
        print "Allocated size of mft entry:", self.m_allocated
        print "File reference to the base file record:", self.m_filereference
        print "Next attribute ID:", self.m_nextattribute
        print "Number of self MFT record:", self.m_mftnumber
        print "Number of attributes:", len(self.m_attributes)
        print "Location", self.m_location

        print "+++"

        for a in self.m_attributes:
            a.attribute_print()
            print "**********"
