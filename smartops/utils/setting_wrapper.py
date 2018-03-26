import datetime
import lazypy
import logging
import os
import os.path

CONFIG_DIR = os.environ.get('SMARTOPS_CONFIG_DIR', '/etc/smartops')
SQLALCHEMY_DATABASE_URI = 'sqlite://'
SQLALCHEMY_DATABASE_POOL_TYPE = 'static'
DEFAULT_LOGLEVEL = 'debug'
DEFAULT_LOGDIR = '/tmp'
DEFAULT_LOGINTERVAL = 1
DEFAULT_LOGINTERVAL_UNIT = 'h'
DEFAULT_LOGFORMAT = (
    '%(asctime)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s')
DEFAULT_LOGBACKUPCOUNT = 5
VENV_HOME = '/Users/xicheng/.virtualenvs/smartops'
CELERYCONFIG_DIR = lazypy.delay(lambda: CONFIG_DIR)
CELERYCONFIG_FILE = ''

if 'SMARTOPS_SETTING' in os.environ:
    SETTING = os.environ['SMARTOPS_SETTING']
else:
    SETTING = '/etc/smartops/setting'

try:
    logging.info('load settings from %s', SETTING)
    execfile(SETTING, globals(), locals())
except Exception as error:
    logging.exception(error)
    raise error
