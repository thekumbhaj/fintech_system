from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""
    
    list_display = ['email', 'full_name', 'kyc_status', 'is_active', 'date_joined']
    list_filter = ['kyc_status', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth')
        }),
        ('KYC Information', {
            'fields': (
                'kyc_status',
                'kyc_submitted_at',
                'kyc_verified_at',
                'document_type',
                'document_number',
                'document_expiry',
            )
        }),
        ('Address', {
            'fields': (
                'address_line1',
                'address_line2',
                'city',
                'state',
                'postal_code',
                'country',
            )
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    
    readonly_fields = ['kyc_submitted_at', 'kyc_verified_at', 'date_joined', 'last_login']
