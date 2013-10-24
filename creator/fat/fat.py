
import struct
import sys
import binascii
import datetime

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


""" ForGe uses NTFS flags - 0x1 = system, 0x2 = directory, 0x4 = regular 
    this class converts from FAT to NTFS flags """

class FlagConverter(object):
    @staticmethod
    def convert_to_ntfs(flag):
        i = 0;
        if flag & FLAG_DIR:
            i |= 0x2
        if flag & FLAG_SYSTEM:
            i |= 0x1
        else:
            i |= 0x4
        return i



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
    def __init__(self,p,data1,data2):
        self.parent = p
        self.t_data1 = data1
        self.t_data2 = data2

        """ ctime """
        c = 256*ord(data1[2]) + ord(data1[1])
        d = 256*ord(data1[4]) + ord(data1[3])

        t_day = d & 31
        t_month = (d & 480) >> 5
        t_year = ((d & 65024) >> 9) + 1980

        t_sec = (c & 31) * 2
        t_min = (c & 2016) >> 5
        t_hour = (c & 63488) >> 11
        if t_day > 0 and t_month > 0:
            self.ctime = datetime.datetime(t_year, t_month, t_day, t_hour, t_min, t_sec)
        else: 
            self.ctime = None

        """ mtime """
        c = 256*ord(data2[1]) + ord(data2[0])
        d = 256*ord(data2[3]) + ord(data2[2])
        t_day = d & 31
        t_month = (d & 480) >> 5
        t_year = ((d & 65024) >> 9) + 1980

        t_sec = (c & 31) * 2
        t_min = (c & 2016) >> 5
        t_hour = (c & 63488) >> 11
        if t_day > 0 and t_month > 0:
            self.mtime = datetime.datetime(t_year, t_month, t_day, t_hour, t_min, t_sec)
        else: 
            self.mtime = None
        
        """ atime """

        d = 256*ord(data1[6]) + ord(data1[5])
        t_day = d & 31
        t_month = (d & 480) >> 5
        t_year = ((d & 65024) >> 9) + 1980

        if t_day > 0 and t_month > 0:
            self.atime = datetime.datetime(t_year, t_month, t_day)
        else: 
            self.atime = None
        
        
    def print_time(self):
        print self.ctime
        print self.mtime
        print self.atime

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
        self.d_unixname = self._unmangle_name(self.d_filename,self.d_extension)
        self.d_flags, = struct.unpack("B",se[11])
        self.d_time = FATTime(self,se[13:20],se[22:26])
        self.d_cluster, = struct.unpack("<H",se[26:28])
        self.d_filesize, = struct.unpack("<I", se[28:32])
        self.d_location = loc+block[1]
        self.d_parentdir = parentdir
        self.d_clusterchain = []
        self.d_slack = None
        self.d_ntfsflags = FlagConverter.convert_to_ntfs(self.d_flags)
        if parentdir:
            self.d_path = self.d_parentdir.d_path + "/" + self.d_unixname
        else:
            self.d_path = "/"+self.d_unixname

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
            print "Cluster:", self.parent.f_fat.get_cluster_chain(self.d_cluster)[0]
            pass
        print "Size:", self.d_filesize
        print "-----"
    def _unmangle_name(self, n, e):
        result = ""
        for c in n:
            if c == " ":
                continue
            result += c

        extresult = ""
        for c in e:
            if c == " ":
                continue
            extresult += c
        
        if extresult == "":
            name = result
        else:
            name = result+"."+extresult
        return name

    def read_file(self):
        if len(self.d_clusterchain) > 0:
            buf = ""
            for i in self.d_clusterchain:
                buf += self.parent.read_cluster(i)
            return buf
        else:
            return None

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
        self.f_slack = []
        self.f_filelist = []
        
    """ returns cluster location in sectors """
    def locate_cluster(self, cl):
        location = self.f_datastart + (cl-2) * self.f_clustersize
        return location

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
        self.print_vbr()

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
            if d.d_cluster > 0:
                d.d_clusterchain = self.f_fat.get_cluster_chain(d.d_cluster)
                if not d.d_flags & FLAG_DIR:
                    last_cluster = d.d_clusterchain[-1]
                    remainder = d.d_filesize % self.f_clustersize
                    slackamount = (remainder / self.f_sectorsize) * self.f_sectorsize
                    slackstart = self.locate_cluster(last_cluster) + self.f_clustersize - slackamount
                    if slackamount > 0:
                        d.d_slack = [slackstart, slackamount, 0]
                        self.f_slack.append([slackstart, slackamount, 0])

            if d.d_flags & FLAG_DIR and d.d_cluster > 0 and d.d_exists:
                dir_stack.append(d)
            if not d.d_flags & FLAG_DIR:
                self.f_filelist.append(d)
        
        while True:
            try:
                nd = dir_stack.pop()
                buf = nd.read_file()
                dirent = self._process_dir(buf)
                for f in dirent:
                    d = DirEntry(self,f,nd,self.locate_cluster(nd.d_cluster))
                    if d.d_cluster > 0:
                        d.d_clusterchain = self.f_fat.get_cluster_chain(d.d_cluster)
                        if not d.d_flags & FLAG_DIR:
                            last_cluster = d.d_clusterchain[-1]
                            remainder = d.d_filesize % self.f_clustersize
                            slackamount = (remainder / self.f_sectorsize) * self.f_sectorsize
                            slackstart = self.locate_cluster(last_cluster) + self.f_clustersize - slackamount
                            if slackamount > 0:
                                d.d_slack = [slackstart, slackamount, 0]
                                self.f_slack.append([slackstart, slackamount, 0])

                    if d.d_flags & FLAG_DIR and d.d_cluster > 0 and d.d_exists:
                        if d.d_filename == ".       " or d.d_filename == "..      ":
                            pass
                        else:
                            dir_stack.append(d)
                    if not d.d_flags & FLAG_DIR:
                        self.f_filelist.append(d)


            except IndexError:
                break

    def read_cluster(self, cluster):
        position = self.f_datastart*self.f_sectorsize + (cluster-2)*self.f_clustersize
        self.fs_fh.seek(position)
        buf = self.fs_fh.read(self.f_clustersize*self.f_sectorsize)
        return buf

    def locate_cluster(self, cluster):
        position = self.f_datastart * self.f_sectorsize + (cluster -2)*self.f_clustersize
        return position

    """ Interface methods """
    def get_file_slack(self):
        return self.f_slack if len (self.f_slack) > 0 else None

    def register_used_file_slack(self, location, used):
        for s in self.f_slack:
            if s[0] == location:
                s[2] = used

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

    def get_list_of_files(self,flags):
        result = []
        for n in self.f_filelist:
            if n.d_ntfsflags == flags:
                result.append(n)
        



# Foo

fs = FATC("/usr/local/forge/Images/pup", "/mnt/image")
fs.fs_init()


