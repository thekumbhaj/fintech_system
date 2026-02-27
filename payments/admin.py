from django.contrib import admin
from .models import PaymentIntent, WebhookEvent


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    """Admin interface for Payment Intent"""
    
    list_display = [
        'gateway_payment_id',
        'user',
        'amount',
        'currency',
        'status',
        'payment_method',
        'created_at',
    ]
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['gateway_payment_id', 'user__email', 'description']
    readonly_fields = [
        'id',
        'gateway_payment_id',
        'gateway_response',
        'created_at',
        'updated_at',
        'succeeded_at',
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'gateway_payment_id', 'user', 'amount', 'currency')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'status', 'description', 'metadata')
        }),
        ('Gateway Response', {
            'fields': ('gateway_response', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'succeeded_at')
        }),
    )


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    """Admin interface for Webhook Event"""
    
    list_display = [
        'event_id',
        'event_type',
        'status',
        'retry_count',
        'created_at',
        'processed_at',
    ]
    list_filter = ['status', 'event_type', 'created_at']
    search_fields = ['event_id', 'event_type']
    readonly_fields = '__all__'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'event_id', 'event_type', 'status')
        }),
        ('Payload', {
            'fields': ('payload',)
        }),
        ('Processing', {
            'fields': ('error_message', 'retry_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at')
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual webhook creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup"""
        return True
