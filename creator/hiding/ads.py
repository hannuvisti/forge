'''
Created on 28 May 2013

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


from random import choice
import sys
from ui.uitools import ForensicError
from ui.uitools import errlog

FLAG_SYSTEM = 0x1
FLAG_DIRECTORY = 0x2
FLAG_REGULAR = 0x4



class HidingMethod(object):
    def __init__(self): 
        self.supported = []
        self.priorityflag = 0
    
        

""" Parameters taken:
    streamname:adsname    use adsname to hide
"""
class AlternateDataStream(HidingMethod):
    '''
    classdocs
    '''

    def __init__(self,filesystem):
        super(AlternateDataStream, self).__init__()
        self.fs = filesystem


    def hide_file(self,hfile,image,param = {}):
        if self.fs.fs_fstype != "ntfs":
            raise ForensicError("Alternate data streams work only on NTFS")
        files = self.fs.get_list_of_files(FLAG_REGULAR)
        stream_name = "ads"
        hr = None

        """ if stream name has been provided, use it, otherwise default to ads"""
        try:
            stream_name = param["streamname"]
        except KeyError:
            pass
        try:
            itr = 0
            while True:
                c = choice(files)
                itr = itr + 1
                if image.check_trivial_usage_status(c.filename) == False:
                    break
                if itr > 20:
                    raise ForensicError("Cannot find unused trivial files")
        except IndexError:
            raise ForensicError("No regular files for ADS")
        targetfile = self.fs.fs_mountpoint + c.filename + ":" + stream_name


        if self.fs.mount_image() != 0:
            raise ForensicError("Cannot mount image")

        try:
            wf = open(targetfile,"w")
            buf = hfile.read()
            wf.write(buf)
            wf.close()

            hr = c.filename+":"+stream_name
        except IOError:
            try:
                wf.close()
            except IOError:
                pass
            finally:
                raise ForensicError("Cannot write to file")

            
    
        if self.fs.dismount_image() != 0:
            raise ForensicError("Cannot dismount image")
        rp = c.filename
        if rp.find("/./") == 0:
            rp = rp[2:]  
        if hr.find("/./") == 0:
            hr = hr[2:]
        return dict(instruction=hr,path=rp)
        

        
        
