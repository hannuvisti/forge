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

from django.forms import ModelForm
from models import Case, Webhistory

class RequestCaseForm(ModelForm):
    class Meta:
        model = Case
        fields = ["name", "owner", "date_created", "filesystem", "size", "amount", "garbage", "fsparam1"]

class RequestWebhistoryForm(ModelForm):
    class Meta:
        model = Webhistory
        fields = ["name"]
