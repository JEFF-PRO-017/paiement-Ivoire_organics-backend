import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()

#TODO FDOSSIER API A SUPPIMER LORS DE LA PRO HORS VERCEL