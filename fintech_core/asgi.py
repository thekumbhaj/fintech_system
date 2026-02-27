"""
ASGI config for fintech_core project.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fintech_core.settings')

application = get_asgi_application()
