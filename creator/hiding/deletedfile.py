'''
Created on 21 Jun 2013

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


""" Params taken: directory:/dir """

class DeletedFile(HidingMethod):
    def __init__(self,filesystem):
        super(DeletedFile, self).__init__()
        self.fs = filesystem


    
    def hide_file(self, hfile, image, param = {}):
        hf = None
        dirs1 = self.fs.get_list_of_files(FLAG_DIRECTORY|FLAG_REGULAR)
        dirs2 = self.fs.get_list_of_files(FLAG_DIRECTORY|FLAG_SYSTEM)
        dirs = dirs1+[dirs2[0]]
        try:
            givendir = param["directory"]
            internalpath = givendir+"/"+os.path.basename(hfile.name)
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

        try:
            if self.fs.mount_image() != 0:
                raise ForensicError("Mount failed")

            tf = open(targetfile, "w")
            tf.write(hfile.read())
            tf.close()
            #os.remove(targetfile)
            if self.fs.dismount_image() != 0:
                raise ForensicError("Dismount failed")
            
        except IOError:
            errlog("cannot write file")
            raise ForensicError("Cannot write file")
        if internalpath.find("/./") == 0:
            internalpath = internalpath[2:]      
        return dict(instruction=hf,todelete=[targetfile])
