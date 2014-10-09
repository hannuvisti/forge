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

from django.conf.urls import patterns, url

from ui import views


urlpatterns = patterns('',
    url(r'^$', views.IndexView, name='index'),
    url(r'^main$', views.IndexView, name='index'),
    url(r'^files$', views.trivial_file_view, name='file'),
    url(r'^secretfiles$', views.secret_file_view, name='file'),
    url(r'^init_db$', views.initDbView, name='file'),
    url(r'^posttrivialfile$', views.post_trivial_view, name='post'), 
    url(r'^postsecretfile$', views.post_secret_view, name='post'),
    url(r'^images/(?P<iid>\d+)/$', views.imageView, name='image'),
    url(r'^images$', views.imageView, name='image'),  
    url(r'^webhistory/(?P<iid>\d+)/$', views.webhistoryView, name='webhistory'),
    url(r'^webhistory$', views.webhistoryView, name='webhistory'),  
    url(r'^solution$', views.solutionView, name='solution'),
    url(r'^solution/(?P<iid>\d+)/$', views.solutionView, name='solution'),
     
    
    #url(r'^(?P<pk>\d+)/$', views.DetailView.as_view(), name='detail'),
    #url(r'^(?P<pk>\d+)/results/$', views.ResultsView.as_view(), name='results'),
    #url(r'^(?P<poll_id>\d+)/vote/$', views.vote, name='vote'),
)
