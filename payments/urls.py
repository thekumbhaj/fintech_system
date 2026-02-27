"""
URL configuration for payments app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, webhook_handler

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('webhook/', webhook_handler, name='payment_webhook'),
    path('', include(router.urls)),
]
