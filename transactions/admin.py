from django.contrib import admin
from .models import Transaction, TransactionLedger


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transaction model"""
    
    list_display = [
        'reference_id',
        'from_user',
        'to_user',
        'amount',
        'transaction_type',
        'status',
        'created_at',
    ]
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['reference_id', 'from_user__email', 'to_user__email', 'description']
    readonly_fields = [
        'id',
        'reference_id',
        'from_balance_before',
        'from_balance_after',
        'to_balance_before',
        'to_balance_after',
        'created_at',
        'updated_at',
        'completed_at',
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'reference_id', 'transaction_type', 'status', 'amount')
        }),
        ('Participants', {
            'fields': ('from_user', 'to_user')
        }),
        ('Balance Tracking', {
            'fields': (
                'from_balance_before',
                'from_balance_after',
                'to_balance_before',
                'to_balance_after',
            )
        }),
        ('Details', {
            'fields': ('description', 'metadata', 'error_message', 'retry_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent manual transaction creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent transaction deletion for audit trail"""
        return False


@admin.register(TransactionLedger)
class TransactionLedgerAdmin(admin.ModelAdmin):
    """Admin interface for Transaction Ledger"""
    
    list_display = [
        'transaction',
        'user',
        'entry_type',
        'amount',
        'balance_after',
        'created_at',
    ]
    list_filter = ['entry_type', 'created_at']
    search_fields = ['transaction__reference_id', 'user__email']
    readonly_fields = '__all__'
    ordering = ['-created_at']
    
    def has_add_permission(self, request):
        """Prevent manual ledger entry creation"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent ledger entry deletion for audit trail"""
        return False
