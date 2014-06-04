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
FLAG_FILESYSTEM = 1
FLAG_RAW = 2
FLAG_TIMELINE = 3

""" params taken:
    delete:True   - deletes file after concatenation """

class ConcatenateFile(HidingMethod):
    def __init__(self,filesystem):
        super(ConcatenateFile, self).__init__()
        self.fs = filesystem
        self.priorityflag = FLAG_FILESYSTEM

    
    def hide_file(self, hfile, image, param = {}):
        files = self.fs.get_list_of_files(FLAG_REGULAR)
        hr = None
        try:
            itr = 0
            while True:
                c = choice(files)
                itr = itr + 1
                if image.check_trivial_usage_status(c.filename) == False:
                    break
                if itr > 20:
                    raise ForensicError("Cannot find unused trivial files")
            chosenfile = c.filename
        except IndexError:
            errlog("No files to target")
            raise ForensicError("no files to target")
        
        if self.fs.mount_image() != 0:
            raise ForensicError("Mount failed")
        
        targetfile = self.fs.fs_mountpoint + chosenfile
        try:
            tfile = open(targetfile, "a")
            tfile.write(hfile.read())
            tfile.close()
            try:
                result_file = hfile.name.rsplit("/",1)[1]
            except IndexError:
                result_file = hfile.name
            hr = chosenfile+"+"+result_file
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
        if chosenfile.find("/./") == 0:
            chosenfile = chosenfile[2:]  
        
        try:
            if param["delete"] == "True":
                return dict(instruction=hr+" DELETED", path=chosenfile, todelete=[targetfile])
        except KeyError:
            return dict(instruction=hr,path=chosenfile)
        
