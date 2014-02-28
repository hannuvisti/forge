'''
Created on 22 Jun 2013

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


""" params taken:
    mark_used: boolean
"""

class UnallocatedSpace(HidingMethod):
    def __init__(self,filesystem):
        super(UnallocatedSpace, self).__init__()
        self.fs = filesystem

        
    def hide_file(self, hfile, param = {}):
        mark_used = False
        try:
            if param["mark_used"] == "True":
                mark_used = True
        except KeyError:
            pass
        try:
            buf = hfile.read()
        except IOError:
            raise ForensicError("cannot read secret file")


        """ Locate enough unallocated space """
        spc = self.fs.locate_unallocated_space(len(buf))
        if spc == -1:
            raise ForensicError("Not enough unallcoated space")

        self.fs.write_location(spc,buf)
        for c in xrange(int(spc/self.fs.f_clustersize), int((spc+len(buf))/self.fs.f_clustersize)):
            self.fs.set_cluster_status(c,1,mark_used)

        hf = "location: "+str(spc)+",length: "+str(len(buf))
        return dict(instruction=hf)

