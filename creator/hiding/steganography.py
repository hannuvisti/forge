'''
Created on 21 May 2014

@author: visti
Copyright 2014 Hannu Visti

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
import uuid
import sys
from subprocess import call

FLAG_SYSTEM = 0x1
FLAG_DIRECTORY = 0x2
FLAG_REGULAR = 0x4


""" Parameters taken:
    passphrase:string  - passphrase to steghide - default foo
    delete:True  - delete target file afterwards
"""

class Steganography(HidingMethod):
    def __init__(self,filesystem):
        super(Steganography, self).__init__()
        self.fs = filesystem


    def hide_file(self, hfile, image, param = {}):
        extensions = ["jpg", "bmp", "wav", "au"]
        files = self.fs.get_list_of_files(FLAG_REGULAR)
        dirs2 = self.fs.get_list_of_files(FLAG_DIRECTORY|FLAG_SYSTEM)
        """ Process all directories and the root directory """
        try:
            passphrase = param["passphrase"]
        except KeyError:
            passphrase = "foo"

        tmpdir = "/tmp/"+str(uuid.uuid4())
        tfname = os.path.basename(hfile.name)
        tmppath = tmpdir+"/"+tfname
        try:
            os.mkdir(tmpdir)
        except:
            raise ForensicError("steganography: cannot create tmp dir")

        try:
            yfile = open(tmppath,"w")
            yfile.write(hfile.read())
            yfile.close()
        except:
            os.rmdir(tmpdir)
            raise ForensicError("steganography: cannot write to %s" % tmppath)

        """ Get a list of candidate files of suitable type """
        cfiles = image.find_trivial_files_by_ext(extensions)

        
        """ try to steghide """
        try:
            if self.fs.mount_image() != 0:
                os.remove(tmppath)
                os.rmdir(tmpdir)
                raise ForensicError("Steganography: mount failed")
            while True:
                c = choice(cfiles)
                if image.check_trivial_usage_status(c) == False:
                    targetfile = self.fs.fs_mountpoint + c
                    result = call(["/usr/bin/steghide", "embed", "-p", passphrase, "-q", 
                                   "-ef", tmppath, "-cf", targetfile, "-e", "none"], shell=False)
                    if result == 0:
                        break
                cfiles.remove(c)
        except IndexError:
            os.remove(tmppath)
            os.rmdir(tmpdir)
            raise ForensicError("No suitable files for steganography")
        except OSError:
            os.remove(tmppath)
            os.rmdir(tmpdir)
            raise ForensicError("steghide does not exist")

        try:
            os.remove(tmppath)
            os.rmdir(tmpdir)
        except:
            raise ForensicError("steganography: cannot remove temp files")
        
        if self.fs.dismount_image() != 0:
            raise ForensicError("Steganography: dismount failed")


        instr = "%s inside %s, passphrase %s" % (tfname, c, passphrase)
        try:
            if param["delete"] == "True":
                return dict(instruction=instr+" DELETED", todelete=[self.fs.fs_mountpoint+c], path=c)
            else:
                return dict(instruction=instr, path=c)
        except KeyError:
            return dict(instruction=instr, path=c)
