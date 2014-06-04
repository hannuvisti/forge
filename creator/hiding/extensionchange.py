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


""" Parameters taken:
    delete:True   - deletes file after changing extension
    use:ext - uses always ext
    notroot:True
"""

class ExtensionChange(HidingMethod):
    def __init__(self,filesystem):
        super(ExtensionChange, self).__init__()
        self.fs = filesystem


    def hide_file(self, hfile, image, param = {}):
        extensions = ["jpg", "com", "zip", "xlsx", "doc", "xls", "exe", "dll", "pdf", "rar"]
        hf = None
        dirs1 = self.fs.get_list_of_files(FLAG_DIRECTORY|FLAG_REGULAR)
        dirs2 = self.fs.get_list_of_files(FLAG_DIRECTORY|FLAG_SYSTEM)
        """ Process all directories and the root directory """
        try:
            if param["notroot"] == "True":
                dirs = dirs1
            else:
                dirs = dirs1+[dirs2[0]]
        except KeyError:
            dirs = dirs1+[dirs2[0]]    

        try:
            short_targetdir=choice(dirs).filename
            internalpath = short_targetdir+"/"+os.path.basename(hfile.name)
            targetfile = self.fs.fs_mountpoint + internalpath
            targetdir = self.fs.fs_mountpoint + short_targetdir
            
            
        except IndexError:
            errlog("No directory for hiding")
            raise ForensicError("No directory for hiding")
        try:
            if self.fs.mount_image() != 0:
                raise ForensicError("Mount failed")

            tf = open(targetfile, "w")
            tf.write(hfile.read())
            tf.close()
            
            """ find extension """
            try:
                mfn,ext = targetfile.rsplit(".",1)
            except ValueError:
                mfn = targetfile
                ext = ""
            try:
                m2,e2 = internalpath.rsplit(".",1)
            except ValueError:
                m2=targetfile

                
            """ remove this extension from the list if it is there """
            try:
                extensions.remove(ext)
            except ValueError:
                pass
            
            
            """ count extensions in target directory """
            exti = {}
            dirt = os.listdir(targetdir)

            for f in dirt:
                try:
                    fn,e = f.rsplit(".",1)
                    try:
                        exti[e] += 1
                    except KeyError:
                        exti[e] = 1
                except ValueError:
                    continue

            """ choose extension """
            try:
                ext_to_use = max(exti,key=exti.get)
            except ValueError:
                ext_to_use = choice(extensions)
            finally:
                if ext_to_use == ext:
                    ext_to_use = choice(extensions)
                try:
                    ext_to_use = param["use"]
                except KeyError:
                    pass
            new_filename = mfn+"."+ext_to_use
            os.rename(targetfile,new_filename)
            hf = m2+"."+ext_to_use        
   

            if self.fs.dismount_image() != 0:
                raise ForensicError("Dismount failed")
            
        except IOError:
            errlog("cannot write file")
            try:
                tf.close()
            except IOError:
                pass
        
            self.fs.dismount_image()
            raise ForensicError("Cannot write file")
        if m2.find("/./") == 0:
            m2 = m2[2:] 
        if hf.find("/./") == 0:
            hf = hf[2:]
        try:
            if param["delete"] == "True":
                return dict(instruction=hf+" DELETED", path=m2+"."+ext_to_use, todelete=[new_filename])
        except KeyError:
            return dict(instruction=hf,path=m2+"."+ext_to_use)
