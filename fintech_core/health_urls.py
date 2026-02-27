"""
Health check endpoints
"""
from django.urls import path
from fintech_core.views import health_check

urlpatterns = [
    path('', health_check, name='health_check'),
]
