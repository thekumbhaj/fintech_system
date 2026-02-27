"""
URL configuration for transactions app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, LedgerViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'ledger', LedgerViewSet, basename='ledger')

urlpatterns = [
    path('', include(router.urls)),
]
