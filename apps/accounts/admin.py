from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'status', 'is_staff')
    list_filter = ('role', 'status', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'role', 'status', 'email_verified', 'phone_verified', 'avatar', 'agency_name', 'bio')}),
    )
