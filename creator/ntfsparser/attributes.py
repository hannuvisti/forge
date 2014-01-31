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
import sys
from tools import _NTFSTime, _hexdump
from tools import _Unpack48, _Pack48
from directory import _DirIndexEntry
from directory import _ParseIndexEntries

def parse_attributes(block):
    """ iterator - returns an attribute from MFT until no more attributes are available
    in which case the iterator exhausts [start,length,flag] """
    
    pq = 0
    while struct.unpack("<I", block[pq:pq+4])[0] != 0xFFFFFFFF:
        r = pq
        l, = struct.unpack("<I", block[pq+4:pq+8])
        pq += l
        yield [r,l,struct.unpack("<I",block[r:r+4])[0]]

class _ResidentAttribute(object):
    """ create a resident attribute. method read_data(start,end) 
    returns a chunk of data. read_data (-1,-1) return all data """
    def __init__(self,attr,parent):
        self.a_size = struct.unpack("<I",attr[16:20])[0]
        self.a_offset = struct.unpack("<H", attr[20:22])[0]
        self.a_padding = attr[22:24]
        self.a_data = attr[self.a_offset:self.a_offset+self.a_size+1]
        self.a_slack = None
        self.parent = parent

    def printout(self):
        print "Resident attribute. Size, Offset:",self.a_size,self.a_offset
        pass
    
    def read_data(self,offset, end):
        if offset == -1:
            return self.a_data
        else:
            if end == -1:
                return self.a_data[offset:]
            else:
                return self.a_data[offset:end]
    def pack_residency(self):
        buf = struct.pack("<I",self.a_size)
        buf += struct.pack("<H",self.a_offset)
        buf += self.a_padding
        return buf
    def locate_data(self,offset):
        return self.parent.m_location+offset+self.a_offset
    def get_slack(self):
        return self.a_slack  
    def init_slack(self):
        self.a_slack = None      
    def printData(self):
        print "Length:", self.a_size

class _NonResidentAttribute(object):
    """ create a non-resident attribute. read_data(start,end) return a chunk of data """
    
    def __init__(self,attr,parent):
        self.a_start_v_cluster = struct.unpack("<Q", attr[16:24])[0]
        self.a_end_v_cluster = struct.unpack("<Q", attr[24:32])[0]
        self.a_runlist_offset = struct.unpack("<H", attr[32:34])[0]
        self.a_compression_unit_size = struct.unpack("<H", attr[34:36])[0]
        self.a_allocated_size_of_content = struct.unpack("<Q", attr[40:48])[0]
        self.a_actual_size_of_content = struct.unpack("<Q", attr[48:56])[0]
        self.a_initialised_size_of_content = struct.unpack("<Q", attr[56:64])[0]
        self.a_size = self.a_actual_size_of_content
        self.a_slack = None
        self.parent = parent

        
        self.a_clusterrun = []
        self.a_clusterlist = []

        
        if self.a_start_v_cluster != 0:
            print "non-zero virtual cluster!"
            return
        i = 0
        ptr = self.a_runlist_offset;
        previous_run = 0
        
        
        while i <= self.a_end_v_cluster:
            nibble = struct.unpack("B",attr[ptr:ptr+1])[0]
            nibble_offset = (nibble & 240) >> 4
            nibble_length = nibble & 15
            
            if nibble_offset == 0:
                break
            nhex = ""
            ptr += 1
            while nibble_length > 0:
                nibble_length -= 1
                nhex = '%02x' % struct.unpack("B",attr[ptr:ptr+1])[0] + nhex
                ptr += 1
            rlength = int(nhex,16)
            nhex = ""
            
            """ This can be negative as well """
            max_of_this_offset = 256 ** nibble_offset
            while nibble_offset > 0:
                nibble_offset -= 1
                nhex = '%02x' % struct.unpack("B",attr[ptr:ptr+1])[0] + nhex
                ptr += 1
            offset_candidate = int(nhex,16)
            if offset_candidate > max_of_this_offset/2:
                offset_candidate = -(max_of_this_offset-offset_candidate)
            offset = offset_candidate + previous_run

            i += rlength
            self.a_clusterrun.append([rlength, offset])
            for a in range(offset, offset+rlength):
                self.a_clusterlist.append(a)
            previous_run = offset
        self.nonres_datablock = attr[16:ptr]

    def _read_cluster(self, filed, clnum):
        gl_clustersize = self.parent.parent.parent.f_clustersize
        filed.seek(clnum*gl_clustersize)
        z = filed.read(gl_clustersize)
        
        return z
    def pack_residency(self):
        return self.nonres_datablock

    def read_data(self,offset, end):
        
        gl_clustersize = self.parent.parent.parent.f_clustersize
        fi = open(self.parent.parent.parent.fs_filename, "r")

        if offset == -1:
            offset = 0
            end = self.a_actual_size_of_content 
        elif end == -1:
            end = self.a_actual_size_of_content - offset

        buf = ""

        # First cluster - may be partial
        cluster = int(offset / gl_clustersize)
        tmp = self._read_cluster(fi, self.a_clusterlist[cluster])
        buf = buf + tmp[offset - cluster*gl_clustersize:offset - cluster*gl_clustersize + end]
        qread = len(buf)

        if qread == end:
            return buf
        cluster += 1
        while True:
            
            tmp = self._read_cluster(fi, self.a_clusterlist[cluster])
            if end - qread > gl_clustersize:
                buf = buf + tmp
                qread += len(tmp)
                cluster += 1
            else:
                buf += tmp[:end - qread]
                break
        fi.close()
        return buf
    
    
    
    def locate_data(self,offset):        
        gl_clustersize = self.parent.parent.parent.f_clustersize
        """ "First cluster - may be partial """
        cluster = int(offset / gl_clustersize)

        br = gl_clustersize * self.a_clusterlist[cluster]
        br += (offset % gl_clustersize)
        return br



    """ slack may be found in the last cluster """
    def init_slack(self):
        try:
            last_cluster = self.a_clusterlist[-1]
        except IndexError:
            return
        
        gl_clustersize = self.parent.parent.parent.f_clustersize
        gl_sectorsize = self.parent.parent.parent.f_sectorsize
        free = self.a_allocated_size_of_content - self.a_actual_size_of_content
        free_start = self.a_actual_size_of_content + (free % gl_sectorsize)
        free_amount = self.a_allocated_size_of_content - free_start

        if free_amount >= gl_clustersize or free_amount == 0:
            self.a_slack = None
            return
        
        start_byte = gl_clustersize * last_cluster + (free_start % gl_clustersize)
        """ init a slack item with absolute start position,
            available space and space used for accounting purposes 
        """
  
        self.a_slack = [start_byte, free_amount, 0]
        
    def get_slack(self):
        return self.a_slack
    
    def printData(self):
        print "Actual size:", self.a_actual_size_of_content
        print "Allocated size:", self.a_allocated_size_of_content
        print "Init size:", self.a_initialised_size_of_content
    
    def printout(self):
        print "Non-resident attribute"
        
class _NTFSAttribute(object):
    """ a parent class is a superclass to all different attributes. No instances of self class alone
    should exist, self is only used in inheritance to define common part in attribute structure """

    a_type = 0
    a_length = 0
    a_resident = False
    a_namelength = 0
    a_nameoffset = 0
    a_flags = 0
    a_attrid = 0
    a_sizeofcontent = 0
    def __init__(self,parent):
        self.a_name = ""
        self.a_type = ""
        self.a_flags = 0;
        self.a_sizeofcontent = 0;
        self.parent = parent
        
    def parse_header(self, header):

        self.a_type = struct.unpack("<I",header[0:4])[0]
        self.a_length = struct.unpack("<I",header[4:8])[0]
        if struct.unpack("B",header[8])[0] == 0:
            self.a_resident = True
        else:
            self.a_resident = False
        self.a_namelength = struct.unpack("B",header[9])[0]
        self.a_nameoffset = struct.unpack("<H", header[10:12])[0]
        self.a_flags = struct.unpack("<H", header[12:14])[0]

        self.a_attrid = struct.unpack("<H", header[14:16])[0]
        if self.a_namelength != 0:
            self.a_name = header[self.a_nameoffset:self.a_nameoffset+self.a_namelength*2].decode("utf-16-le")
        else:
            self.a_name = None

    def pack_header(self):
        buf=struct.pack("<II",self.a_type,self.a_length)
        if self.a_resident:
            buf += struct.pack("B",0)
        else:
            buf += struct.pack("B",0x80)
        buf += struct.pack("B",self.a_namelength)
        buf += struct.pack("<HHH", self.a_nameoffset, self.a_flags, self.a_attrid)
        if self.a_namelength != 0:
            buf += self.a_name.encode("utf-16-le")
        return buf        

    def A_print_header(self):
        print "Type:", self.attribute_name()
        print "Length:", self.a_length
        print "Location offset", self.a_location
        print "Resident:", self.a_resident
        print "Name length:", self.a_namelength
        print "Name offset:", self.a_nameoffset
        if self.a_name != None:
            print "Name:", self.a_name
        print "Flags:", self.a_flags

class _NTFSAttributeStandard(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeStandard, self).__init__(parent)
    def init_attribute(self,attr,offset):
        self.a_location = offset
        self.parse_header(attr)
        if self.a_resident == True:
            self.a_content = _ResidentAttribute(attr, self)
        else:
            self.a_content = _NonResidentAttribute(attr, self)

        self.a_time = _NTFSTime(self.a_content.read_data(0,32))
        self.a_dospermissions, = struct.unpack("<I", self.a_content.read_data(32,36))
        self.a_maxversions, = struct.unpack("<I", self.a_content.read_data(36,40))
        self.a_versionnumber, = struct.unpack("<I", self.a_content.read_data(40,44))
        self.a_classid, = struct.unpack("<I", self.a_content.read_data(44,48))
        #        self.a_ownerid = struct.unpack("<I", self.a_content.read_data(48,52))[0]

    def attribute_print(self):
        self.A_print_header()
        self.a_time.printtime()
        print "Version number", self.a_versionnumber
        print "Class id", self.a_classid
    def write_attribute(self):
        buf =  self.pack_header()
        buf += self.a_content.pack_residency()
        buf += self.a_time.raw_time()
        buf += struct.pack("<IIII",self.a_dospermissions,self.a_maxversions,
                           self.a_versionnumber, self.a_classid)
        self.parent.parent.write_location(self.a_location,buf)
        
        
    def attribute_name(self):
        return "Standard"

class _NTFSAttributeList(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeList, self).__init__(parent)
    def init_attribute(self,attr, offset):
        self.a_location = offset
        self.parse_header(attr)
        if self.a_resident == True:
            self.a_content = _ResidentAttribute(attr,self)
        else:
            self.a_content = _NonResidentAttribute(attr,self)
    
    def write_attribute(self):
        return
        
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "Attribute list"

class _NTFSAttributeFileName(_NTFSAttribute):

    def __init__(self,parent):
        super(_NTFSAttributeFileName, self).__init__(parent)
        self.a_ascname = ""
    def init_attribute(self,attr, offset):
        self.a_location = offset
        self.parse_header(attr)
        if self.a_resident == True:
            self.a_content = _ResidentAttribute(attr, self)
        else:
            self.a_content = _NonResidentAttribute(attr, self)
        self.a_parentdir = _Unpack48(self.a_content.read_data(0,6))
        self.a_parentsq = struct.unpack("<H", self.a_content.read_data(6,8))[0]
        self.a_time = _NTFSTime(self.a_content.read_data(8,40))
        self.a_logicalfilesize = struct.unpack("<Q", self.a_content.read_data(40,48))[0]
        self.a_sizeondisk = struct.unpack("<Q", self.a_content.read_data(48,56))[0]
        self.a_fflags = struct.unpack("<I", self.a_content.read_data(56,60))[0]
        self.a_reparse = struct.unpack("<I", self.a_content.read_data(60,64))[0]
        self.a_namelen = struct.unpack("B", self.a_content.read_data(64,65))[0]
        self.a_nametype = struct.unpack("B", self.a_content.read_data(65,66))[0]
        self.a_name = self.a_content.read_data(66,66+(self.a_namelen*2))
        self.a_ascname = self.a_name.decode("utf-16-le")
        #_hexdump(attr)

    def write_attribute(self):
        buf =  self.pack_header()
        buf += self.a_content.pack_residency()
        buf += _Pack48(self.a_parentdir)
        buf += struct.pack("<H",self.a_parentsq)
        buf += self.a_time.raw_time()
        buf += struct.pack("<QQ",self.a_logicalfilesize,self.a_sizeondisk)
        buf += struct.pack("<II", self.a_fflags,self.a_reparse)
        buf += struct.pack("BB", self.a_namelen, self.a_nametype)
        buf += self.a_name
        """ padded to 8 bytes """
        buf += '\x00'* (self.a_length - len(buf))
        
        self.parent.parent.write_location(self.a_location,buf)

    def attribute_print(self):
        self.A_print_header()
        print "Parentdir:", self.a_parentdir
        print "Logical file size:", self.a_logicalfilesize
        print "Flags:", self.a_flags
        #        print "Name:", self.a_name
        print "Asc name:", self.a_ascname
        self.a_time.printtime()

        
    def attribute_name(self):
        return "File name"

    def change_name(self,name,flag):
        if flag == True:
            self.a_ascname = name
            self.a_name = self.a_ascname.encode("utf-16-le")
            self.a_namelen = len(name)
        else:
            self.a_name = name
            self.a_ascname = self.a_name.decode("utf-16-le")
            self.a_namelen = len(self.a_ascname)

class _NTFSAttributeVolumeVersion(_NTFSAttribute):

    def __init__(self,parent):
        super(_NTFSAttributeVolumeVersion, self).__init__(parent)
    def init_attribute(self,attr,offset):
        self.a_location = offset
        self.parse_header(attr)
        if self.a_resident == True:
            self.a_content = _ResidentAttribute(attr, self)
        else:
            self.a_content = _NonResidentAttribute(attr, self)
    def write_attribute(self):
        return
    def attribute_print(self):
        self.A_print_header()

    def attribute_name(self):
        return "Volume version"

class _NTFSAttributeObjectId(_NTFSAttribute):

    def __init__(self,parent):
        super(_NTFSAttributeObjectId, self).__init__(parent)

    def init_attribute(self,attr,offset):
        self.a_location = offset
        self.parse_header(attr)
        if self.a_resident == True:
            self.a_content = _ResidentAttribute(attr, self)
        else:
            self.a_content = _NonResidentAttribute(attr, self)
    def write_attribute(self):
        return
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "Object ID"

class _NTFSAttributeSecurityDescriptor(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeSecurityDescriptor, self).__init__(parent)
    def init_attribute(self,attr, offset):
        pass

    def write_attribute(self):
        return    
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "Security descriptor"

class _NTFSAttributeVolumeName(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeVolumeName, self).__init__(parent)
    def init_attribute(self,attr,offset):
        pass
    def write_attribute(self):
        return
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "Volume name"

class _NTFSAttributeVolumeInformation(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeVolumeInformation, self).__init__(parent)
    def init_attribute(self,attr,offset):
        pass
    def write_attribute(self):
        return
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "Volume information"

class _NTFSAttributeData(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeData, self).__init__(parent)
    def init_attribute(self,attr,offset):
        self.a_location = offset
        self.parse_header(attr)
        if self.a_resident == True:
            self.a_content = _ResidentAttribute(attr, self)
        else:
            self.a_content = _NonResidentAttribute(attr, self)
        if self.parent.m_mftnumber > 16:
            self.a_content.init_slack()
            
    def attribute_print(self):
        self.A_print_header()
        self.a_content.printData()
    def write_attribute(self):
        return
    def attribute_name(self):
        return "Data"

class _NTFSAttributeIndexRoot(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeIndexRoot, self).__init__(parent)       
    def init_attribute(self,attr,offset):
        self.a_location = offset
        self.parse_header(attr)
        if self.a_resident == True:
            self.a_content = _ResidentAttribute(attr, self)
        else:
            self.a_content = _NonResidentAttribute(attr, self)

        
        # Index root
        self.a_ir_attrtype, self.a_ir_collation_rule, self.a_ir_siae = struct.unpack("<III", self.a_content.read_data(0,12))
        self.a_ir_clusters, = struct.unpack("B", self.a_content.read_data(12,13))
        
        # Index node header
        self.a_ir_offset,self.a_ir_totalsize,self.a_ir_allocatedsize = struct.unpack("<III", self.a_content.read_data(16,28))
        self.a_ir_flags, = struct.unpack("B", self.a_content.read_data(28,29))
        loc = self.a_ir_offset + 16
        


        if self.a_ir_flags & 1:
            self.a_smallindex = False
        else:
            self.a_smallindex = True
        
        egen = _ParseIndexEntries(self.a_content.read_data(loc,-1))
        for dirtmp in egen:
            tmp = dirtmp[0]
            entry = _DirIndexEntry(self,dirtmp[1]+self.a_location+loc)
            entry.init_entry(tmp, self.a_ir_attrtype)     
            self.parent.m_ir_entry.append(entry)

            if entry.vcn != -1:
                self.parent.m_dirtmp.append(entry.vcn)

        self.parent.set_directory()  
        
    def write_attribute(self):
        return       
    def attribute_print(self):
        self.A_print_header()

    def attribute_name(self):
        return "Index root"

class _NTFSAttributeIndexAllocation(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeIndexAllocation, self).__init__(parent)
        
    def init_attribute(self,attr,offset):
        self.a_location = offset
        
        """ every index buffer has a magic number, called VCN number. 
            This has nothing to do with virtual clusters. Find the index buffer
            corresponding to VCN and return it """
            
        def __returnIndexBlock(data,vcn):
            
            indexsize = self.parent.parent.f_indexbuffersize
            idx = 0
            while idx < len(data):
                datmp = data[idx*indexsize:(idx+1)*indexsize]
                clnum, = struct.unpack("<Q",datmp[0x10:0x18])
                if clnum == vcn:
                    return [datmp,idx*indexsize]
                idx += 1
            
            """ this should not happen """
            print "Index buffer not found, exiting", vcn
            exit(1)
     
        self.parse_header(attr)
        if self.a_resident == True:
            self.a_content = _ResidentAttribute(attr, self)
        else:
            self.a_content = _NonResidentAttribute(attr, self)
        wholedata = self.a_content.read_data(-1,-1)
        
        
        """ try to make sense of b-trees """
        
        
        while True:
            try:
                vcn = self.parent.m_dirtmp.pop()
                data,vcnloc = __returnIndexBlock(wholedata,vcn)
                baselocation = self.a_content.locate_data(vcnloc)
                """ Fixup array """
                updateoffset = struct.unpack("<H", data[4:6])[0]
                fixup = struct.unpack("<H", data[6:8])[0]
                x = updateoffset + 2
                y = fixup - 1
                mtmp = data
    
                for z in range (0,y):
                    f = data[x] + data[x+1]
                    x += 2
                    mtmp = mtmp[:z*512+510]+f+mtmp[(z+1)*512:]
                
                """ Find the exact length of index entries """
                self.a_ir_endsequence, self.a_ir_endbuffer = struct.unpack("<II", mtmp[0x1c:0x24])
                """ process entries """
                
                egen = _ParseIndexEntries(mtmp[0x40:self.a_ir_endsequence+0x18])            
                for dirtmp in egen:
                    tmp = dirtmp[0]
                    entry = _DirIndexEntry(self,baselocation+dirtmp[1]+0x40)
                    entry.init_entry(tmp, 0x30)
                    self.parent.m_ir_entry.append(entry)
                    if entry.flags & 1 != 0 and entry.vcn != 0:
                        self.parent.m_dirtmp.append(entry.vcn)
                    #__entry.print_entry()
            except IndexError:
                self.parent.set_directory()
                break
        """ Index buffer done """
    def write_attribute(self):
        return        
       
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "Index allocation"

class _NTFSAttributeBitmap(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeBitmap, self).__init__(parent)
        self.a_bitmap = ""

    def init_attribute(self,attr,offset):
        self.a_location = offset
        self.parse_header(attr)
        if self.a_resident == True:
            self.a_content = _ResidentAttribute(attr, self)
        else:
            self.a_content = _NonResidentAttribute(attr, self)
        
        self.a_bitmap = self.a_content.read_data(-1, -1)

    def get_bit(self,number):
        byte = int(number/8)
        bit = number - byte*8
        return (self.a_bitmap[byte] >> bit) & 1

    def modify_bit(self,number, value, image_write=False):
        if value < 0 or value > 1:
            return False
        byte = int(number/8)
        bit = number - byte*8
        
        old_value = ord(self.a_bitmap[byte])
        bloc = (2**bit)*value
        new_value = struct.pack ("B",old_value | bloc)
        
        self.a_bitmap = self.a_bitmap[:byte]+new_value+self.a_bitmap[byte+1:]
        if image_write:
            self.parent.parent.write_location(self.a_location+byte, new_value)
        

    def write_attribute(self):
        return
        """ This write does not add anything. It modifies existing bytes only """
        buf =  self.pack_header()
        buf += self.a_content.pack_residency()
        buf += self.a_bitmap
        """ padded to 8 bytes """
        buf += '\x00'* (self.a_length - len(buf))
        
        self.parent.parent.write_location(self.a_location,buf)
    
    def attribute_print(self):
        self.A_print_header()
        print "Bitmap length:", len(self.a_bitmap)
    def attribute_name(self):
        return "Bitmap"

class _NTFSAttributeSymLink(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeSymLink, self).__init__(parent)
    def init_attribute(self,attr,offset):
        pass
    def write_attribute(self):
        return
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "Symbolic link"

class _NTFSAttributeReparsePoint(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeReparsePoint, self).__init__(parent)
    def init_attribute(self,attr,offset):
        pass
    def write_attribute(self):
        return
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "Reparse point"

class _NTFSAttributeEaInformation(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeEaInformation, self).__init__(parent)
    def init_attribute(self,attr,offset):
        pass
    def write_attribute(self):
        return
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "EA Information"

class _NTFSAttributeEa(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeEa, self).__init__(parent)
    def init_attribute(self,attr,offset):
        pass
    def write_attribute(self):
        return
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "EA"

class _NTFSAttributePropertySet(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributePropertySet, self).__init__(parent)
    def init_attribute(self,attr,offset):
        pass
    def write_attribute(self):
        return
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "Property set"
    
class _NTFSAttributeLoggedUtilityStream(_NTFSAttribute):
    def __init__(self,parent):
        super(_NTFSAttributeLoggedUtilityStream, self).__init__(parent)
    def init_attribute(self,attr,offset):
        pass
    def write_attribute(self):
        return
    def attribute_print(self):
        self.A_print_header()
    def attribute_name(self):
        return "Logged utility stream"

# self list selects the correct attribute class based on the attribute number
NTFS_ATTRIBUTES = {0x10:_NTFSAttributeStandard,0x20:_NTFSAttributeList,
                   0x30:_NTFSAttributeFileName, 0x40:_NTFSAttributeVolumeVersion,
                   0x50:_NTFSAttributeObjectId,0x60:_NTFSAttributeVolumeName,
                   0x70:_NTFSAttributeVolumeInformation,0x80:_NTFSAttributeData,
                   0x90:_NTFSAttributeIndexRoot,0xa0:_NTFSAttributeIndexAllocation,
                   0xb0:_NTFSAttributeBitmap,0xc0:_NTFSAttributeSymLink,
                   0xd0:_NTFSAttributeEaInformation,0xe0:_NTFSAttributeEa,
                   0xf0:_NTFSAttributePropertySet,0x100:_NTFSAttributeLoggedUtilityStream}
