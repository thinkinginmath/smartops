"""utility switch to virtual env."""
import os
import os.path
import site
import sys

from smartops.utils import setting_wrapper as setting

virtual_env = setting.VENV_HOME
activate_this = '%s/bin/activate_this.py' % virtual_env
execfile(activate_this, dict(__file__=activate_this))
site.addsitedir('%s/lib/python2.6/site-packages' % virtual_env)
if virtual_env not in sys.path:
    sys.path.append(virtual_env)
os.environ['PYTHON_EGG_CACHE'] = '/tmp/.egg'
