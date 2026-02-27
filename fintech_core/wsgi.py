"""
WSGI config for fintech_core project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fintech_core.settings')

application = get_wsgi_application()
