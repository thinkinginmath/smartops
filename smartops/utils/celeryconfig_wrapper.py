import logging
import os.path

from smartops.utils import setting_wrapper as setting


CELERY_RESULT_BACKEND = 'amqp://'


BROKER_URL = 'amqp://guest:guest@rabbit:5672'

CELERY_IMPORTS = ('smartops.tasks.tasks',)

if setting.CELERYCONFIG_FILE:
    CELERY_CONFIG = os.path.join(
        str(setting.CELERYCONFIG_DIR),
        str(setting.CELERYCONFIG_FILE))

    try:
        logging.info('Loading celery config from %s', CELERY_CONFIG)
        execfile(CELERY_CONFIG, globals(), locals())
    except Exception as error:
        logging.exception(error)
        raise error
