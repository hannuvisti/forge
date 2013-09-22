'''
Created on 6 Aug 2013

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

from hiding.ads import HidingMethod
from random import choice
from ui.uitools import errlog
from ui.uitools import ForensicError
import os
import sys

FLAG_SYSTEM = 0x1
FLAG_DIRECTORY = 0x2
FLAG_REGULAR = 0x4
FLAG_FILESYSTEM = 1
FLAG_RAW = 2
FLAG_TIMELINE = 3

""" params taken:
    directory:/path   - copies the file to /path """

class DoNotHideFile(HidingMethod):
    def __init__(self,filesystem):
        super(DoNotHideFile, self).__init__()
        self.fs = filesystem
        self.priorityflag = FLAG_FILESYSTEM

    
    def hide_file(self, hfile, param = {}):
        hf = None
        dirs1 = self.fs.get_list_of_files(FLAG_DIRECTORY|FLAG_REGULAR)
        dirs2 = self.fs.get_list_of_files(FLAG_DIRECTORY|FLAG_SYSTEM)
        dirs = dirs1+[dirs2[0]]
        try:
            newdir = param["directory"]
            internalpath = newdir+"/"+os.path.basename(hfile.name)
            targetfile = self.fs.fs_mountpoint + internalpath
            hf = internalpath
        except KeyError:
            try:
                dpr = choice(dirs)
                if dpr.filename != "/.":
                    targetdir=dpr.filename
                else: 
                    targetdir=""
                
                internalpath = targetdir+"/"+os.path.basename(hfile.name)
                targetfile = self.fs.fs_mountpoint + internalpath
                hf = internalpath
            
            except IndexError:
                raise ForensicError("No directory for hiding")
        finally:
            if self.fs.mount_image() != 0:
                raise ForensicError("Mount failed")
            dpath = os.path.dirname(targetfile)
            if not os.path.exists(dpath):
                try:
                    os.makedirs(dpath)
                except IOError:
                    raise ForensicError("Unable to create directory %s" % dpath)
        try:
            tfile = open(targetfile, "w")
            tfile.write(hfile.read())
            tfile.close()

        except IOError:
            errlog("Unable to write")
            try:
                tfile.close()
            except IOError:
                pass
            self.fs.dismount_image()
            raise ForensicError("Unable to write")
        finally:
            self.fs.dismount_image()
        return dict(instruction=hf,path=internalpath)
        
