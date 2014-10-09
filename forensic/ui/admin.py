'''
Created on 30 May 2013

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

from django.contrib import admin
from ui.models import User,Case,Image,TrivialFileItem, FileSystem, HidingMethod
from ui.models import Webhistory,TrivialStrategy,Url,SearchEngine
from ui.models import TrivialObject, SecretStrategy, HiddenObject, SecretFileItem
from django.forms import ModelForm
import datetime


#class UserInline(admin.TabularInline):
#    model = User
#    extra = 3


class CaseAdminForm(ModelForm):
    class Meta:
        model = Case
        
    def __init__(self, *args, **kwargs):
        try:
            kwargs['initial'].update({"date_created" : datetime.datetime.now(),"weekvariance":26})
        except KeyError:
            kwargs['initial'] = {}
        
        super(CaseAdminForm,self).__init__(*args, **kwargs)

class FileSystemAdmin(admin.ModelAdmin):
    list_display= ("name", "pythonpath", "pythoncreatecommand")
    search_fields = ["name"]

class HidingMethodAdmin(admin.ModelAdmin):
    list_display= ("name", "priority", "pythonpath", "pythonhideclass")
    search_fields = ["name"]        

class CaseAdmin(admin.ModelAdmin):
    
    #inlines = [UserInline]
    list_display = ('name', 'owner', 'date_created', 'amount','filesystem', 'roottime', 'weekvariance')
    list_filter = ['date_created']
    search_fields = ['name']
    date_hierarchy = 'date_created'
    form = CaseAdminForm

class WebhistoryAdmin(admin.ModelAdmin):
    list_display=('name', 'date_created')
    search_fields = ['name']

class UserAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "valid_until")
    search_fields = ['name']
    #form = UserAdminForm

class FileAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "file")
    search_fields = ['name']   
    
class SecretFileAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "file") 
    list_editable = ["group"]

class UrlAdmin(admin.ModelAdmin):
    list_display=("case", "url", "num_clicks", "click_depth", "date_clicked", "group")
    list_editable = ["url","group", "num_clicks", "click_depth"]

class SearchengineAdmin(admin.ModelAdmin):
    list_display=("case", "engine", "search_string", "click_result", "click_depth", "date_clicked", "group")
    list_editable = ["search_string", "click_result", "click_depth", "group"]

class TrivialStrategyAdmin(admin.ModelAdmin):
    list_display=("case", "type", "exact", "quantity", "path", "dirtime")

class TrivialObjectAdmin(admin.ModelAdmin):
    list_display=("image", "file", "inuse", "path")
    
class SecretStrategyAdmin(admin.ModelAdmin):
    list_display = ("case", "method", "group", "filetime", "action", "actiontime", "instruction")
    
class HiddenObjectAdmin(admin.ModelAdmin):
    list_display = ("image", "file", "method", "filetime", "action", "actiontime", "location")

class ImageAdmin(admin.ModelAdmin):
    list_display=("case", "seqno", "weekvariance", "filename")
    search_fields = ["case"]
    
  
admin.site.register(Case, CaseAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Url, UrlAdmin)
admin.site.register(SearchEngine, SearchengineAdmin)
admin.site.register(Webhistory, WebhistoryAdmin)
admin.site.register(TrivialFileItem, FileAdmin)
admin.site.register(SecretFileItem, SecretFileAdmin)
admin.site.register(FileSystem, FileSystemAdmin)
admin.site.register(HidingMethod, HidingMethodAdmin)
admin.site.register(TrivialStrategy, TrivialStrategyAdmin)
admin.site.register(TrivialObject, TrivialObjectAdmin)

admin.site.register(SecretStrategy, SecretStrategyAdmin)
admin.site.register(HiddenObject, HiddenObjectAdmin)
admin.site.register(Image, ImageAdmin)
