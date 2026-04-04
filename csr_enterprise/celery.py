import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'csr_enterprise.settings')

app = Celery('csr_enterprise')
# Load task modules from all registered Django apps.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()