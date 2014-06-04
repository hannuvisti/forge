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


""" params taken: """

class FileSlack(HidingMethod):
    def __init__(self,filesystem):
        super(FileSlack, self).__init__()
        self.fs = filesystem

        
    def hide_file(self, hfile, image, param = {}):
        slack = self.fs.get_file_slack()
        hf = ""
        if slack == None:
            errlog("Not enough slack space")
            raise ForensicError("Not enough slack space")
        available_slack = 0
        for i in slack:
            if i[2] == 0:
                available_slack = available_slack + i[1]
        try:
            buf = hfile.read()
        except IOError:
            raise ForensicError("cannot read secret file")

        if available_slack < len(buf):
            raise ForensicError("Not enough slack")
        bytes_written = 0
        bytes_remaining = len(buf)
        for i in slack:
            if i[2] != 0:
                continue
            if bytes_remaining <= i[1]:
                self.fs.write_location(i[0],buf[bytes_written:])
                hf = hf+","+str(i[0])+":"+str(bytes_remaining)
                self.fs.register_used_file_slack(i[0],bytes_remaining)
                if hf.find(",") == 0:
                    hf = hf[1:]
                return dict(instruction=hf)
            self.fs.write_location(i[0],buf[bytes_written:bytes_written+i[1]])
            self.fs.register_used_file_slack(i[0], i[1])
            hf = hf+","+str(i[0])+":"+str(i[1])   
            bytes_written += i[1] 
            bytes_remaining -= i[1]           
        """ this should never be reached """

        raise ForensicError ("This should not happen")
