
import struct
import sys
import binascii

from subprocess import call

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


HELPER = "/usr/local/forge/chelper/chelper"
FLAG_HIDDEN = 0x2
FLAG_SYSTEM = 0x4
FLAG_DIR = 0x16

sys.path.append("/usr/local/forge/creator")

class FileHandler(object):
    gl_filename = ""
    def __init__(self):
        self.gl_filename = ""

    @staticmethod
    def SetFileName(name,handle):
        FileHandler.gl_filename = name
        FileHandler.gl_fh = handle
    @staticmethod
    def GetFileName():
        return FileHandler.gl_filename

    @staticmethod
    def GetHandle():
        return FileHandler.gl_fh


class FATTime(object):
    def __init__(self,p,data):
        self.parent = p
        self.t_data = data

class DirEntry(object):
    def __init__(self, parent, block,parentdir,loc):
        self.parent = parent
        se = block[0][-1]
        q = se[0]
        if ord(q) == 0xE5 or ord(q) == 0:
            self.d_exists = False
        else:
            self.d_exists = True
        self.d_filename = se[0:8]
        self.d_extension = se[8:11]
        self.d_flags, = struct.unpack("B",se[11])
        self.d_time = FATTime(self,se[22:26])
        self.d_cluster, = struct.unpack("<H",se[26:28])
        self.d_filesize, = struct.unpack("<I", se[28:32])
        self.d_location = loc+block[1]
        self.d_parentdir = parentdir

        lname = ""
        if len(block[0]) > 1:
            temp = block[0][0:-1]
            temp.reverse()
            for e in temp:
                lname = lname + e[1:11] + e[14:26] + e[28:32]
            p = lname.find("\x00\x00")
            if p != 0:
                self.d_longname = lname[0:p]
            else:
                self.d_longname = "This should not happen"
        else:
            self.d_longname = ""

    def print_entry(self):
        print "Filename:", self.d_filename,".",self.d_extension
        print "Long name:", self.d_longname
        print "Entry loc:", self.d_location
        print "Flags:", self.d_flags
        if self.d_cluster > 0:
            print "Cluster:", self.parent.f_fat.get_cluster_chain(self.d_cluster)
        print "Size:", self.d_filesize
        print "-----"

class FatTable(object):
    def __init__(self,buf,loc,par):
        self.rawdata = buf
        print "FAT length",len(self.rawdata)
        self.parent = par
        self.location = loc
        if self.parent.fs_fstype == "FAT16":
            self.bytes = 16
        if self.parent.fs_fstype == "FAT12":
            self.bytes = 12
        if self.parent.fs_fstype == "FAT32":
            self.bytes = 32

    def get_cluster_value(self,cluster):
        start_byte = self.bytes*cluster
        start_char = int(start_byte/8)
        if self.bytes == 16:
            return struct.unpack("<H",self.rawdata[start_char:start_char+2])[0]
        if self.bytes == 32:
            return struct.unpack("<I",self.rawdata[start_char:start_char+4])[0]
        return "foo"

    def get_cluster_chain(self,cl=0):
        eoc = 2**self.bytes-1
        t = cl
        result = [cl]
        while True:
            s = self.get_cluster_value(t)
            if s == 0 or s == eoc:
                return result
            result.append(s)
            t = s

class FileSystemC(object):
    def __init__(self, fname, mountpoint="/mnt/image"):
        self.fs_sectorsize=0
        self.fs_size=0
        self.fs_fstype=""
        self.fs_mountpoint = mountpoint
        self.fs_fh = open(fname, "r")
        self.fs_filename = fname
        FileHandler.SetFileName(fname,self.fs_fh)
        if len(self.fs_filename.rsplit('/',1)) == 1:
            self.fs_shortname = self.fs_filename
        else:
            self.fs_shortname = self.fs_filename.rsplit('/',1)[1]

class FATC(FileSystemC):

    def __init__(self,fname,mountpoint="/mnt/image"):
        super(FATC, self).__init__(fname,mountpoint)
        self.fs_fstype = "FAT16"
        self.f_mounted = False
        self.f_filelist = []


    def fat_vbr_init(self, vbr):
        self.f_sectorsize, = struct.unpack("<H", vbr[11:13])
        self.f_clustersize = self.f_sectorsize * struct.unpack("B",vbr[13])[0]
        self.f_reserved, = struct.unpack("<H", vbr[14:16])
        self.f_numberoffats, = struct.unpack("B", vbr[16])
        self.f_rootentries, = struct.unpack("<H", vbr[17:19])
        _small_sector, = struct.unpack("<H", vbr[19:21])
        _large_sector, = struct.unpack("<I", vbr[32:36])
        self.f_numofsectors = _small_sector if _small_sector > 0 else _large_sector
        _small_fat, = struct.unpack("<H",vbr[22:24])
        _large_fat, = struct.unpack("<I",vbr[36:40])
        self.f_fatsize = _small_fat if _small_fat > 0 else _large_fat
        self.f_rootstart = self.f_reserved + self.f_numberoffats*self.f_fatsize
        self.f_datastart = self.f_rootstart + (self.f_rootentries*32)/self.f_sectorsize
        


    def print_vbr(self):
        print "FS type: ", self.fs_fstype
        print "Sector size: ", self.f_sectorsize
        print "Cluster size: ", self.f_clustersize
        print "Reserved sectors: ", self.f_reserved
        print "Number of FATs: ", self.f_numberoffats
        print "Root entries: ", self.f_rootentries
        print "Number of sectors in FS: ", self.f_numofsectors
        print "FAT size: ", self.f_fatsize
        print "root start sector: ", self.f_rootstart
        print "data start sector: ", self.f_datastart

    def _process_dir(self,buf):
        i=0
        stack=[]
        while i < len(buf):
            if ord(buf[i]) == 0:
                return
            flags = ord(buf[i+0x0b])
            if flags == 0x0f:
                stack.append(buf[i:i+32])
                i+=32
                continue
            stack.append(buf[i:i+32])
            i += 32
            result = stack
            stack = []
            yield [result,i-32]
            

    def fs_init(self):
        self.fs_fh.seek(0)
        buf = self.fs_fh.read(512)
        self.fat_vbr_init(buf)
        #self.print_vbr()

        self.fs_fh.seek(self.f_sectorsize*self.f_reserved)
        buf = self.fs_fh.read(self.f_fatsize*self.f_sectorsize)
        self.f_fat = FatTable(buf,512,self)

        
        self.fs_fh.seek(self.f_sectorsize*self.f_rootstart)
        rootdir = self.fs_fh.read(self.f_rootentries * 32)
        """ process root dir """
        dir_stack = []
        dirent = self._process_dir(rootdir)
        for f in dirent:
            d = DirEntry(self,f, None, self.f_sectorsize*self.f_rootstart)
            d.print_entry()
            if d.d_flags & FLAG_DIR and d.d_cluster > 0 and d.d_exists:
                dir_stack.append(d)
        
        """        try:
            while True:
                nd = dir_stack.pop()
                buf = self.read_cluster(nd.d_cluster)
                dirent = self._process_dir(buf)
        """
    def mount_image(self):
        result = call([HELPER, "attach", self.fs_fstype, self.fs_shortname], shell=False)
        if result == 0:
            self.f_mounted = True
        return result
    def dismount_image(self):
        result = call([HELPER, "detach"], shell=False)
        if result == 0:
            self.f_mounted = False
        return result

    def read_cluster(self, cluster):
        self.fs_fh.seek((self.f_datastart+(cluster*self.f_clustersize)) * self.f_sectorsize)
        buf = self.fs_fh.read(self.f_clustersize*self.f_sectorsize)
        return buf



# Foo

fs = FATC("/usr/local/forge/Images/pup", "/mnt/image")
fs.fs_init()


