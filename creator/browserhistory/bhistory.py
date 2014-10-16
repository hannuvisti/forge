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
from hiding.ads import HidingMethod
from ui.uitools import errlog
from ui.uitools import ForensicError
from ui.uitools import Chelper
from subprocess import check_output
from subprocess import CalledProcessError
from shutil import copyfile
from traceback import format_exc
from time import sleep
import uuid
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

class BrowserHistory(HidingMethod):
    def __init__(self,filesystem=None):
        super(BrowserHistory, self).__init__()
        self.chelper = Chelper()
        self.fs = filesystem

    def prepare_container(self):
        try:
            a=check_output([self.chelper.binary, "lxc", "lxc-destroy"], 
                           shell=False)
            a=check_output([self.chelper.binary, "lxc", "lxc-create"], 
                           shell=False)
            sleep (3)
            a=check_output([self.chelper.binary, "lxc", "lxc-attach", "nowait", "silent",
                            "Xvfb", ":0", "-screen", "0", "1024x768x24"], 
                           shell=False)
            sleep (3)
        except CalledProcessError as e:
            print e
            raise ForensicError("exec_file")

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
            b = check_output([self.chelper.binary,"lxc", "lxc-attach", "wait", 
                              "vocal",
                              "su", "-", "forge", "-c", 
                              "python /tmp/wh.py"], shell=False)
            return b.rstrip()
        except CalledProcessError as e:
            print e
            raise ForensicError

    def hide_url(self, trivial_urls=[], secret_urls=[], amount=1,
                 trivial_searches=[], secret_searches=[], param={}):
        
        self.get_file("/tmp/forge.TMP")
        fi = open("/tmp/forge.TMP", "a")
        
        for u in trivial_urls:
            if u.num_clicks < 1:
                fi.write("b.open_page(\"%s\")" % u.url)
                fi.write("\n")
            else:
                fi.write("b.do_n_clicks(\"%s\", %d,random=False)" % 
                         (u.url, u.num_clicks))
                fi.write("\n")


        for u in secret_urls:
            if u.num_clicks < 1:
                fi.write("b.open_page(\"%s\")" % u.url)
                fi.write("\n")
            else:
                fi.write("b.do_n_clicks(\"%s\", %d,random=False)" % 
                         (u.url, u.num_clicks))
                fi.write("\n")

        fi.write ("b.close()")
        fi.write("\n")
        fi.close()

        tmpdir = "/tmp/Forge."+uuid.uuid4().hex
        try:
            os.mkdir(tmpdir)
        except:
            raise ForensicError("make temp dir")

        self.prepare_container()
        self.send_file("/tmp/forge.TMP")
        
        resl=[]
        i=0
        while i < amount:
            i += 1
            result_path = self.exec_file()
            if result_path == "None":
                resl.append(dict(status="Fail", fname=None,size=0))
            else:
                try:
                    rloc = check_output([self.chelper.binary,"lxc", "copy_result", 
                                         self.chelper.rootdir+result_path, tmpdir], 
                                        shell=False).rstrip()
                except:
                    raise ForensicError("copy results");

                try:
                    historysize = str(int(os.path.getsize(rloc)/1000000)+8)+"M"
                except:
                    raise ForensicError("Cannot stat results")

                resl.append(dict(status="OK", fname=rloc, size=historysize))
            
        self.delete_container()

        return dict(status=0,message="",results=resl,tdir=tmpdir)
