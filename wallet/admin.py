from django.contrib import admin
from .models import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Admin interface for Wallet model"""
    
    list_display = ['id', 'user', 'balance', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'balance')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual wallet creation - they're auto-created via signals"""
        return False
