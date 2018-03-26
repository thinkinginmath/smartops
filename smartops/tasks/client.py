from celery import Celery
from smartops.tasks import celeryconfig

celery = Celery(__name__)
celery.config_from_object(celeryconfig)
