from django.contrib import admin
from apps.engagements.models import Favorite, Enquiry, Lead, PropertyVisit, Notification

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'created_at')

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ('property', 'sender_user', 'created_at')
    search_fields = ('property__title', 'sender_user__username')

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('property', 'lead_user', 'owner_user', 'status', 'created_at')
    list_filter = ('status',)

@admin.register(PropertyVisit)
class PropertyVisitAdmin(admin.ModelAdmin):
    list_display = ('property', 'visitor_user', 'visit_date', 'status')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'channel', 'is_read', 'created_at')
    list_filter = ('is_read', 'channel')
