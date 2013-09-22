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




'''
Note: This file is not used by ForGe but it can be used to 
act as wrapper to the NTFS parser
'''


import sys
from subprocess import call
from ntfsc import NTFSC
import datetime
from ui.uitools import ForensicError

HELPER = "/home/forensic/chelper"

    
def NTFSCreateImage(name, size, garbage, clustersize=2048):
    #ntfs=NTFSC("/home/visti/Project/Images/image-ntfs")
    #ntfs.fs_init()
    print >>sys.stderr, "this should not happen"
    return -1
    #ntfs=NTFSC("/home/visti/Project/Images/image-ntfs", "/mnt/image")
    if len(name) <= 8:
        __imagename = name
    else:
        __imagename = name[:8]
    
    if garbage:
        __fill = "random"
    else:
        __fill = "clean"
         
    __result = call([HELPER, "create", "ntfs", str(size), str(clustersize), __imagename, __fill, name], shell=False)
    return __result

ntfs=NTFSC("/home/visti/Project/Images/testi-2", "/mnt/image")
ntfs.fs_init()

try:
    m = ntfs.find_file_by_path("/doc/neocv.doc")
    m.mft_display()
    dt = datetime.datetime(2005,2,4,12,32,42)
    rt = datetime.datetime(2010,1,7,1,59,59)
    ntfs.change_time("/doc/neocv.doc", dict(all=dt,etime=rt))
    m.mft_display()

except ForensicError:
    pass

#ntfs.fs_display()
#ntfs.fs_display()
