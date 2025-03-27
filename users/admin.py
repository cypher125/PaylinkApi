from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, VTPassTransaction


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Admin configuration for custom User model"""
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'vtpass_account_id', 'vtpass_balance')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'vtpass_account_id')
    
    # Add custom fields to the admin form
    fieldsets = UserAdmin.fieldsets + (
        ('VTPass Information', {'fields': ('vtpass_account_id', 'vtpass_balance', 'preferred_network')}),
        ('Additional Information', {'fields': ('phone_number', 'date_of_birth', 'address', 'state', 'pin')}),
        ('Banking Information', {'fields': ('bank_name', 'account_number', 'account_name', 'bvn')}),
    )


@admin.register(VTPassTransaction)
class VTPassTransactionAdmin(admin.ModelAdmin):
    """Admin configuration for VTPassTransaction model"""
    list_display = ('user', 'transaction_type', 'service_id', 'amount', 'status', 'created_at')
    list_filter = ('status', 'transaction_type', 'created_at')
    search_fields = ('user__email', 'user__username', 'transaction_type', 'service_id', 'request_id', 'vtpass_reference')
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'user', 'transaction_type', 'service_id', 'amount', 'phone_number', 
                      'email', 'request_id', 'vtpass_reference', 'response_data', 'created_at', 'updated_at')
