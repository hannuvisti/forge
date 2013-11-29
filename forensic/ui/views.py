'''
Copyright 2013 Hannu Visti

This file is part of ForGe forensic test image generator.
ForGe is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ForGe.  If not, see <http://www.gnu.org/licenses/>.
'''

# Create your views here.

from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views import generic

from django.db import DatabaseError
import sys
import datetime
from django.core.context_processors import csrf
from django.shortcuts import render, get_object_or_404, render_to_response
from ui.forms import RequestCaseForm
from ui.uitools import errlog

from ui.models import Case, TrivialFileItem, User, FileSystem, HidingMethod, SecretFileItem, SecretStrategy, Image
from ui.models import HiddenObject, TrivialObject

class Selection():
    selected = 0
    
    @staticmethod
    def getSelection():
        return Selection.selected
    
    @staticmethod
    def setSelection(selection):
        Selection.selected = selection
        
    
def getFileType(content):
    
    __document_list = ["application/pdf","application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       "application/msword","application/vnd.oasis.opendocument.text",
                       "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                       "application/rtf",
                       "application/vnd.ms-excel",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
    __application_list = ["application/octet-stream", "application/x-shellscript",
                          "application/x-ms-dos-executable","application/x-java-archive"]
    __archive_list = ["application/zip","application/x-gzip","application/x-rar"]
    __text_list = ["text/plain"]
    __audio_list = ["audio/mpeg"]
    
    if content.startswith("image/"):
        return 0
    if content in __document_list:
        return 1
    if content in __application_list:
        return 6
    if content in __archive_list:
        return 9
    if content.startswith("text/"):
        return 8
    if content.startswith("audio/"):
        return 4
    if content.startswith("video/"):
        return 5
    
    return 7

def initDbView(request):
    foo = User.objects.all()
    if len(foo) == 0:
        u1 = User(name="forge", role=0, valid_until="2013-12-31")
        u1.save()
        f = FileSystem(name="NTFS", pythonpath="ntfsparser.ntfsc",pythoncreatecommand="NTFSCreateImage", 
                       fsclass = "NTFSC")
        f.save()
        f = FileSystem(name="FAT12", pythonpath="fat.fat",pythoncreatecommand="FAT12CreateImage", 
                       fsclass = "FATC")
        f.save()
        f = FileSystem(name="FAT16", pythonpath="fat.fat",pythoncreatecommand="FAT16CreateImage", 
                       fsclass = "FATC")
        f.save()
        f = FileSystem(name="FAT32", pythonpath="fat.fat",pythoncreatecommand="FAT32CreateImage", 
                       fsclass = "FATC")
        f.save()
        f = FileSystem(name="FAT", pythonpath="fat.fat",pythoncreatecommand="FATGenericCreateImage", 
                       fsclass = "FATC")
        f.save()
        h = HidingMethod(name="ADS", priority = 1, pythonpath="hiding.ads", pythonhideclass = "AlternateDataStream")
        h.save()
        h = HidingMethod(name="Deleted file", priority = 2, pythonpath="hiding.deletedfile", pythonhideclass = "DeletedFile")
        h.save()
        h = HidingMethod(name="Extension change", priority = 1, pythonpath="hiding.extensionchange", pythonhideclass="ExtensionChange")
        h.save()
        h = HidingMethod(name="Concatenate", priority = 1, pythonpath="hiding.concatenate", pythonhideclass="ConcatenateFile")
        h.save()
        h = HidingMethod(name="File slack", priority = 4, pythonpath="hiding.fileslack", pythonhideclass="FileSlack")
        h.save()
        h = HidingMethod(name="Not hidden", priority = 3, pythonpath="hiding.donothide", pythonhideclass="DoNotHideFile")
        h.save()
        c=Case(name="casetest", owner=User.objects.get(name="forge"), date_created="2013-06-01", 
               size="10M", amount=3, garbage=False,fsparam1=8, weekvariance=26, filesystem= FileSystem.objects.get(name="NTFS"),
               roottime=datetime.datetime(2010,7,16,3,42,42))
        c.save()
        c.trivialstrategy_set.create(type=0, quantity=2,  exact = True, path="/holiday",
                                     dirtime = datetime.datetime(2010,12,24,17,0,0))
        c.trivialstrategy_set.create(type=1, quantity=2, exact = True, path="/doc",
                                     dirtime = datetime.datetime(2011,2,28,9,30,15))
        c.secretstrategy_set.create(method=h, group = 1, filetime = datetime.datetime(2008,5,25,10,42,32))
        c.save()
        
    return HttpResponse("ok")

def IndexView(request):
    
    if request.method == "POST":
        click = request.POST.getlist("click2")
        if not click:
            sys.stderr.write("no click")
        else:
            Selection.setSelection(int(click[0]))
            __tmp, = Case.objects.filter(pk=Selection.getSelection())
            sys.stderr.write(__tmp.owner.name)
            
        table = Case.objects.all()
        return render(request, "ui/main.html", {'active_cases': table, 'selected_case': __tmp}) 
    else:
        __tmp = None
        table = Case.objects.all()
        return render(request, "ui/main.html", {'active_cases': table, 'selected_case': __tmp}) 

def trivial_file_view(request):
    
    if request.method == "POST":
        """click = request.POST.getlist("click2")
        if not click:
            sys.stderr.write("no click")
        else:
            Selection.setSelection(int(click[0]))
            __tmp, = Case.objects.filter(pk=Selection.getSelection())
            sys.stderr.write(__tmp.owner.name)
            
        table = Case.objects.all()"""
        return render(request, "ui/files.html", {"cfunction": "posttrivialfile", "instruction": "Drag and drop trivial files here"}) 
    else:

        return render(request, "ui/files.html", {"cfunction": "posttrivialfile", "instruction": "Drag and drop trivial files here"}) 

def post_trivial_view(request):
    if request.method == "POST":
        
        tfile = request.FILES['file']
        ft = getFileType(tfile.content_type)
        if ft == 7:
            print >>sys.stderr, tfile.content_type
        
        

        t = TrivialFileItem(name=tfile.name, type=ft,file=tfile)
        try:
            t.save()
        except DatabaseError:
            try:
                t.save()
            except DatabaseError:
                pass
        
 
    return render(request, "ui/files.html", {"cfunction": "posttrivialfile", "instruction": "Drag and drop trivial files here"}) 

def secret_file_view(request):
    return render(request, "ui/files.html", {"cfunction": "postsecretfile", "instruction": "Drag and drop secret files here"})
def post_secret_view(request):
    if request.method == "POST":
        
        sfile = request.FILES['file']

        t = SecretFileItem(name=sfile.name, file = sfile, group = 0)
        try:
            t.save()
        except DatabaseError:
            try:
                t.save()
            except DatabaseError:
                errlog("can't post secret file")
                pass
        
 
    return render(request, "ui/files.html", {"cfunction": "postsecretfile", "instruction": "Drag and drop secret files here"}) 


        
    
def imageView(request, iid=-1):
    if request.method == "POST":
        
        click = request.POST.getlist("click2")
        if click:
            Selection.setSelection(int(click[0]))
            return HttpResponseRedirect("/ui/images"+"/"+click[0])
        form = RequestCaseForm(request.POST)

        if u'create' in request.POST:
            if iid == -1:
                return HttpResponseRedirect("/ui/images")
            case = Case.objects.get(pk=iid)
            if not case:
                return HttpResponseRedirect("/ui/images")
            qres = case.processCase()
            if qres:
                return render(request, "ui/creationreport.html", 
                              {"case":case, "success": qres[0], "notsuccess": qres[1]})
            else:
                return HttpResponseRedirect("/ui/images")
        return HttpResponseRedirect("/ui/images")
    else:
        table = Case.objects.all() 
        if iid == -1:     
            form = RequestCaseForm()
        else:
            try:
                c, = Case.objects.filter(pk=iid)
                form = RequestCaseForm(instance=c)
            except ValueError:
                return HttpResponseRedirect("/ui/images")
        
    return render(request, "ui/images.html", {"form": form, "active_cases": table})
 
def solutionView(request, iid=-1):
    table = Case.objects.all()
    if request.method == "POST":
        click = request.POST.getlist("click2") 
        chosen_image = request.POST.getlist("chosenimage")
        foo_bar = request.POST.items()
        if iid != -1 and u'submit' in request.POST:
            if not chosen_image:
                return HttpResponseRedirect("/ui/solution"+"/"+str(iid))
            images = Image.objects.filter(case = iid)
            

            this_case = Case.objects.filter(pk=iid)[0]
            this_image = Image.objects.filter(pk=int(chosen_image[0]))[0]
            this_trivial = TrivialObject.objects.filter(image=this_image)
            this_secret = HiddenObject.objects.filter(image=this_image)        
            if not images:
                return HttpResponseRedirect("/ui/solution")
            #return render(request, "ui/solution.html", { "active_cases": table, "created_images": images})  
            return render(request, "ui/report.html", {"case": this_case, "timage": this_image, 
                                                      "trivial": this_trivial, "secret": this_secret}) 
        if click:
            Selection.setSelection(int(click[0]))
            return HttpResponseRedirect("/ui/solution"+"/"+click[0])





        return HttpResponseRedirect("/ui/solution")
     

    else:
         
        if iid == -1:     
            pass
        else:
            try:
                images = Image.objects.filter(case = iid)

                if not images:
                    return HttpResponseRedirect("/ui/solution")
                return render(request, "ui/solution.html", { "active_cases": table, "created_images": images})  
            except ValueError:
                return HttpResponseRedirect("/ui/solution")
        
    return render(request, "ui/solution.html", { "active_cases": table})
       

 
    
