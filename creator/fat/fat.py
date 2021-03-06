
import struct
import sys
import binascii
import datetime

from subprocess import call
from ui.uitools import ForensicError
from ui.uitools import Chelper
from ntfsparser.ntfsc import FileEntry
from random import randint


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


FLAG_HIDDEN = 0x2
FLAG_SYSTEM = 0x4
FLAG_DIR = 0x16





def FAT16CreateImage(name,size,clustersize,garbage,parameters={}):

    if len(name) <= 8:
        imagename = name
    else:
        imagename = name[:8]
        
    if garbage:
        fill = "random"
    else:
        fill = "clean"

    result = call([Chelper().binary,"create","FAT16",str(size),str(clustersize),str(512), imagename,fill,name], shell=False)
    return result

def FAT12CreateImage(name,size,clustersize,garbage,parameters={}):

    if len(name) <= 8:
        imagename = name
    else:
        imagename = name[:8]
        
    if garbage:
        fill = "random"
    else:
        fill = "clean"

    result = call([Chelper().binary,"create","FAT12",str(size),str(clustersize),str(512), imagename,fill,name], shell=False)
    return result

def FAT32CreateImage(name,size,clustersize,garbage,parameters={}):

    if len(name) <= 8:
        imagename = name
    else:
        imagename = name[:8]
        
    if garbage:
        fill = "random"
    else:
        fill = "clean"

    result = call([Chelper().binary,"create","FAT32",str(size),str(clustersize),str(512), imagename,fill,name], shell=False)
    return result

def FATGenericCreateImage(name,size,clustersize,garbage,parameters={}):

    if len(name) <= 8:
        imagename = name
    else:
        imagename = name[:8]
        
    if garbage:
        fill = "random"
    else:
        fill = "clean"

    result = call([Chelper().binary,"create","GENERICFAT",str(size),str(clustersize),str(512), imagename,fill,name], shell=False)
    return result


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

class DummyTime(object):
    def __init__(self,p,date=None):
        self.parent = p
        self.t_data1="       "
        self.t_data2="    "
        if not date:
            date = datetime.datetime(2010,1,1,1,1,1)

        self.mtime = self.ctime = self.atime = date

    def change_atime(self,newtime):
        return
    def change_mtime(self,newtime):
        return
    def change_ctime(self,newtime):
        return
    def change_all_times(self,newtime):
        return
    def print_entry(self):
        print "Dummy time"



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

    def _modify_binary_data(self):

        if self.ctime != None:
            d = ((self.ctime.year - 1980) << 9) | (self.ctime.month << 5) | self.ctime.day
            c = (self.ctime.hour << 11) | (self.ctime.minute << 5) | (self.ctime.second/2)
            q = struct.pack("<H",c)
            r = struct.pack("<H",d)
            self.t_data1 = self.t_data1[0]+q[0]+q[1]+r[0]+r[1]+self.t_data1[5]+self.t_data1[6]

        if self.atime != None:
            d = ((self.atime.year - 1980) << 9) | (self.atime.month << 5) | self.atime.day
            q = struct.pack("<H",d)
            self.t_data1 = self.t_data1[0:5] + q[0] + q[1]
        
        if self.mtime != None:
            d = ((self.mtime.year - 1980) << 9) | (self.mtime.month << 5) | self.mtime.day
            c = (self.mtime.hour << 11) | (self.mtime.minute << 5) | (self.mtime.second/2)
            q = struct.pack("<H",c)
            r = struct.pack("<H",d)
            self.t_data2 = q[0]+q[1]+r[0]+r[1]
            

        
    def change_atime(self,newtime):
        self.atime = newtime
        self._modify_binary_data()
    def change_mtime(self,newtime):
        self.mtime = newtime
        self._modify_binary_data()
    def change_ctime(self,newtime):
        self.ctime = newtime
        self._modify_binary_data()
    def change_all_times(self,newtime):
        self.change_atime(newtime)
        self.change_mtime(newtime)
        self.change_ctime(newtime)

        
    def print_entry(self):
        print self.ctime
        print self.mtime
        print self.atime

class DirEntry(object):
    def __init__(self, parent, block,parentdir,loc, dummy={}):
        self.parent = parent
        self.d_dummy = False
        if dummy:
            self.d_parentdir = parentdir
            self.d_flags = dummy["flags"]
            self.d_dummy = True
            self.d_cluster = 0
            self.d_filename = ""
            self.d_exists = True
            self.d_extension = ""
            self.d_ntfsflags = FlagConverter.convert_to_ntfs(self.d_flags)
            self.d_location = -42000
            self.d_filesize = 0
            self.d_time = DummyTime(self)
            self.d_slack = None
            self.d_unixname = ""
            self.d_longname = dummy["name"]
            self.d_clusterchain = []
            if parentdir:
                self.d_longpath = self.d_parentdir.d_longpath + unicode("/",errors="strict") + self.d_longname
            else:
                self.d_longpath = unicode('/',errors="strict")+self.d_longname
            return

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

        lname = ""
        if len(block[0]) > 1:
            temp = block[0][0:-1]
            temp.reverse()
            for e in temp:
                lname = lname + e[1:11] + e[14:26] + e[28:32]
            p = lname.find("\x00\x00")
            if p != -1:
                if p%2 != 0:
                    p = p+1
                #self.d_longname = unicode(lname[0:p],errors="ignore",encoding="utf-16-le")
                try:
                    self.d_longname = lname[0:p].decode("utf-16-le")
                except UnicodeDecodeError:
                    print self.d_unixname
                    _hexdump(lname)
                    exit(1)
            else:
                self.d_longname = lname.decode("utf-16-le")
        else:
            #self.d_longname = unicode(self.d_unixname,errors="ignore",encoding="utf-16-le")
            self.d_longname = unicode(self.d_unixname,errors="ignore")

        if parentdir:
            self.d_path = self.d_parentdir.d_path + "/" + self.d_unixname
            self.d_longpath = self.d_parentdir.d_longpath + unicode("/",errors="strict") + self.d_longname
        else:
            self.d_path = '/'+self.d_unixname
            self.d_longpath = unicode('/',errors="strict")+self.d_longname


    def print_entry(self):
        print "Filename:", self.d_filename,".",self.d_extension
        print "Long name:", "X"+self.d_longname+"x"
        print "Unix name:", "X"+self.d_unixname+"x"
        print "Entry loc:", self.d_location
        print "Flags:", self.d_flags
        print "Start cluster:", self.d_cluster
        if self.d_cluster > 0:
            print "Cluster:", self.parent.f_fat.get_cluster_chain(self.d_cluster)[0]
            pass
        print "Size:", self.d_filesize
        print "Path:", self.d_longpath
        self.d_time.print_entry()
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
        if self.d_dummy:
            return None
        if len(self.d_clusterchain) > 0:
            buf = ""
            for i in self.d_clusterchain:
                buf += self.parent.read_cluster(i)
            return buf
        else:
            return None
    def write_timestamps(self):
        if self.d_dummy:
            return None
        self.parent.write_location(self.d_location+13,self.d_time.t_data1)
        self.parent.write_location(self.d_location+22,self.d_time.t_data2)

    def change_all_times(self, times):
        self.d_time.change_all_times(times)
        self.write_timestamps()
    def change_atime(self,times):
        self.d_time.change_atime(times)
        self.write_timestamps()
    def change_ctime(self,times):
        self.d_time.change_ctime(times)
        self.write_timestamps()
    def change_mtime(self,times):
        self.d_time.change_mtime(times)
        self.write_timestamps()

class FatTable(object):
    def __init__(self,buf,loc,par):
        self.rawdata = buf
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
        #print cluster,start_byte, start_char, len(self.rawdata),self.bytes
        #_hexdump(self.rawdata)
        if self.bytes == 16:
            return struct.unpack("<H",self.rawdata[start_char:start_char+2])[0]
        if self.bytes == 32:
            return struct.unpack("<I",self.rawdata[start_char:start_char+4])[0]
        if self.bytes == 12:
            if cluster % 2 != 0:
                #hi = (ord(self.rawdata[start_char+1]) & 15) << 8
                #lo = (ord(self.rawdata[start_char])) 
                hi = (ord(self.rawdata[start_char+1])) << 4
                lo = (ord(self.rawdata[start_char]) & 240) >> 4 
            else:
                #hi = (ord(self.rawdata[start_char+1])) << 4
                #lo = (ord(self.rawdata[start_char]) & 240) >> 4
                hi = (ord(self.rawdata[start_char+1]) & 15) << 8
                lo = (ord(self.rawdata[start_char])) 
            fatvalue = hi | lo
            return fatvalue
                
        return -1

    def get_cluster_chain(self,cl=0):
        eoc = 2**self.bytes-1
        if self.bytes == 32:
            eoc = 0x0fffffff
        t = cl
        result = [cl]
        while True:
            s = self.get_cluster_value(t)
            if s == 0 or s == eoc:
                return result
            if self.bytes == 12 and s >= 0xff0:
                return result
            result.append(s)
            t = s

    def init_fat(self, clusters):
        self.ftb = []
        self.maxclus = clusters-1
        ctmp = 0
        for ctmp in range (0,clusters):
            cv = self.get_cluster_value(ctmp)
            if cv == -1:
                print ctmp
                raise ForensicError("Cluster out of bounds")
            else:
                self.ftb.append(cv)
        pass

    """
    This method finds n consecutive empty clusters. Then marks them
    temporarily as used """

    def find_consecutive_empty(self, n):
        c = 0
        # Random attempt
        while c < 20:
            y = randint(20, self.maxclus-n)
            expected = True
            for w in range(y,y+n):
                if self.ftb[w] != 0:
                    expected = False
            if expected == True:
                for w in range (y,y+n):
                    self.ftb[w] = -1
                return w
            c += 1
        #Sequential attempt
        for y in range(20, self.maxclus-n):
            expected = True
            for w in range(y,y+n):
                if self.ftb[w] != 0:
                    expected = False
            if expected == True:
                for w in range (y,y+n):
                    self.ftb[w] = -1
                return w
        #Sequential attempt fails
        return -1


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
        #self.fs_fstype = ""
        self.f_mounted = False
        self.f_filelist = []
        self.helper = Chelper()
        """ first set fs_fstype variable 

        try:
            gfile = open(fname,"r")
            vbr = gfile.read(512)
            gfile.close()
        except IOError:
            raise ForensicError("Can't init filesystem type")
        fstype_string, = struct.unpack("5s",vbr[54:59])
        if fstype_string == "FAT12":
            self.fs_fstype = "FAT12"
        if fstype_string == "FAT16":
            self.fs_fstype = "FAT16"
        if self.fs_fstype == "":
            fstype_string, = struct.unpack("5s", vbr[82:87])
            print >>sys.stderr, fstype_string
            if fstype_string == "FAT32":
                self.fs_fstype == "FAT32"
            else:
                raise ForensicError("Unknown FAT FS type")
        """

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
        self.f_entrylist = []
        self.f_numofclusters = self.f_numofsectors / struct.unpack("B", vbr[13])[0]
        fstype_string, = struct.unpack("5s",vbr[54:59])
        if fstype_string == "FAT12":
            self.fs_fstype = "FAT12"
        if fstype_string == "FAT16":
            self.fs_fstype = "FAT16"
        if self.fs_fstype == "":
            fstype_string, = struct.unpack("5s", vbr[82:87])
            if fstype_string == "FAT32":
                self.fs_fstype = "FAT32"
            else:
                raise ForensicError("Unknown FAT FS type")
        
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

        self.fs_fh.seek(self.f_sectorsize*self.f_reserved)
        buf = self.fs_fh.read(self.f_fatsize*self.f_sectorsize)
        self.f_fat = FatTable(buf,512,self)
        self.f_fat.init_fat(self.f_numofclusters)
        
        self.fs_fh.seek(self.f_sectorsize*self.f_rootstart)
        if self.fs_fstype == "FAT12" or self.fs_fstype == "FAT16":
            rootdir = self.fs_fh.read(self.f_rootentries * 32)
        if self.fs_fstype == "FAT32":
            rootdir = self.fs_fh.read(2048)
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
                    if d.d_filename == ".       " or d.d_filename == "..      ":
                        pass
                    else:
                        self.f_filelist.append(d)


            except IndexError:
                break
        """ Create a dummy entry for root dir """
        ddict = {}
        ddict["name"] = "."
        ddict["flags"] = FLAG_DIR
        dummyroot = DirEntry(self,"",None,0,dummy=ddict)
        self.f_filelist.append(dummyroot)

        """ Create FileEntry structures """
        i=0
        for q in self.f_filelist:
            fe = FileEntry(i,q.d_longpath,q.d_ntfsflags,q)
            i += 1
            self.f_entrylist.append(fe)

    def read_cluster(self, cluster):
        position = self.f_datastart*self.f_sectorsize + (cluster-2)*self.f_clustersize
        self.fs_fh.seek(position)
        buf = self.fs_fh.read(self.f_clustersize)
        return buf

    def locate_cluster(self, cluster):
        position = self.f_datastart * self.f_sectorsize + (cluster -2)*self.f_clustersize
        return position



            
    """ Interface methods """
    def fs_finalise(self):
        pass

    def write_location(self, position, data):
        try:
            wh = open(self.fs_filename,"r+b");
            wh.seek(position)
            wh.write(data)
            wh.close()
        except IOError:
            raise ForensicError("Cannot write to image")

    def get_file_slack(self):
        return self.f_slack if len (self.f_slack) > 0 else None

    def register_used_file_slack(self, location, used):
        for s in self.f_slack:
            if s[0] == location:
                s[2] = used

    def mount_image(self):
        result = call([self.helper.binary, "attach", self.fs_fstype, self.fs_shortname], shell=False)
        if result == 0:
            self.f_mounted = True
        return result
    def dismount_image(self):
        result = call([self.helper.binary, "detach"], shell=False)
        if result == 0:
            self.f_mounted = False
        return result

    def get_list_of_files(self,flags):
        result = []
        for n in self.f_entrylist:
            if n.get_flags() == flags:
                result.append(n)
        
        return result

    def find_file_by_path(self,path):
        if len(path) > 2:
            if path[:2] == "//":
                path = path[1:]
        for f in self.f_entrylist:
            s = f.get_file_name()
            if s == path:
                return f
        emessage = "File not found: "+path
        raise ForensicError(emessage)

    def locate_unallocated_space(self, datasize):
        required = int(datasize / self.f_clustersize) +1
        q = self.f_fat.find_consecutive_empty(required)
        if q == -1:
            raise ForensicError("Not enough unallocated space")
        return self.locate_cluster(q)

    def set_cluster_status(self,a,b,c):
        pass

    def change_time(self,fname,btime):
        atime=ctime=mtime=None
        try:
            atime=ctime=mtime=btime["all"]
        except KeyError:
            pass

        try:
            atime=btime["atime"]
        except KeyError:
            pass
        try:
            ctime=btime["ctime"]
        except KeyError:
            pass
        try:
            mtime=btime["mtime"]
        except KeyError:
            pass

        try:
            m = self.find_file_by_path(fname).link
            if atime:
                m.change_atime(atime)
            if mtime:
                m.change_mtime(mtime)
            if ctime:
                m.change_ctime(ctime)
        except ForensicError:
            raise

    def implement_action(self,act):

        fname = act[0]
        action = act[1]
        try:
            m = self.find_file_by_path(fname).link
        except ForensicError:
            raise
        result=""

        try:
            actiontime = action["Read"]
            #btime = dict(atime=actiontime)
            m.change_atime(actiontime)
            result += "File read %s" % actiontime      
        except KeyError:
            pass

        try:
            actiontime = action["Rename"]
            btime = {}
            btime["ctime"] = stdtime.ctime
            btime["atime"] = stdtime.atime
            btime["etime"] = stdtime.etime
            btime["mtime"] = stdtime.mtime
            m.change_fname_time(btime)
            btime = {}
            btime["atime"] = actiontime
            btime["etime"] = actiontime
            m.change_std_time(btime)
            result += "File renamed %s" % actiontime
        except KeyError:
            pass
        try:
            actiontime = action["Edit"]
            m.change_atime(actiontime)
            m.change_mtime(actiontime)
            result += "File edited %s" % actiontime
        except KeyError:
            pass

        try:
            actiontime = action["Copy"]
            m.change_mtime(actiontime)
            result += "File copied %s" % actiontime
        except KeyError:
            pass

        try:
            actiontime = action["Move"]
            m.change_mtime(actiontime)
            m.change_ctime(actiontime)
            result += "File moved %s" % actiontime
        except KeyError:
            pass



