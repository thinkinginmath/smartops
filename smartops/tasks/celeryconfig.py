import os, sys
from smartops.utils import setting_wrapper as setting


CELERY_IMPORTS = ('smartops.tasks.tasks',)
CELERYCONFIG_FILE = setting.CELERYCONFIG_FILE

try:
    execfile(CELERYCONFIG_FILE, globals(), locals())
except Exception as e:
    raise e
