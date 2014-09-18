'''
Created on 18 Sep 2014

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
from random import choice
from ui.uitools import errlog
from ui.uitools import ForensicError
from ui.uitools import Chelper
from subprocess import check_output
from subprocess import CalledProcessError
from shutil import copyfile
from traceback import format_exc

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

class BrowserHistory(object):
    def __init__(self,filesystem=None):
        self.chelper = Chelper()
        self.prepare_container()

    def prepare_container(self):
        try:
            a=check_output([self.chelper.binary, "lxc", "lxc-destroy"], 
                           shell=False)
            a=check_output([self.chelper.binary, "lxc", "lxc-create"], 
                           shell=False)
            a=check_output([self.chelper.binary, "lxc", "process_webdrive"], 
                           shell=False)
        except CalledProcessError as e:
            print e
            raise ForensicError("prepare_container")

    def delete_container(self):
        try:
            a=check_output([self.chelper.binary, "lxc", "lxc-destroy"], 
                           shell=False)
        except CalledProcessError as e:
           print e 
           raise ForensicError("delete_container")

    def get_file(self, dst):
        try:
            copyfile(self.chelper.wsrc, dst)
        except:
            raise ForensicError("get_file")

    def send_file(self,src):
        try:
            a=check_output([self.chelper.binary, "lxc", "copy_file",src], 
                           shell=False)
        except CalledProcessError as e:
            format_exc()
            raise ForensicError("send_file")

    def exec_file(self):
        try:
            a=check_output([self.chelper.binary, "lxc", "lxc-attach", "nowait",
                            "Xvfb", ":0", "-screen", "0", "1024x768x24"], 
                           shell=False)
        except CalledProcessError as e:
            print e
            raise ForensicError("exec_file")


        try:
            b = check_output([self.chelper.binary,"lxc", "lxc-attach", "wait",
                              "su", "-", "forge", "-c", 
                              "python /tmp/wh.py"], shell=False)
            print b
        except CalledProcessError as e:
            print e
            raise ForensicError

b=BrowserHistory()
b.get_file("/tmp/xyzzy")
b.send_file("/tmp/xyzzy")

b.exec_file()


