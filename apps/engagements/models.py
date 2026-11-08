from django.db import models
from django.conf import settings
from apps.properties.models import Property, ListingPurposeChoices, PropertyCategoryChoices, PropertyType, FurnishingChoices, PossessionStatusChoices
from apps.locations.models import City, Locality

class LeadStatusChoices(models.TextChoices):
    NEW = 'NEW', 'New'
    CONTACTED = 'CONTACTED', 'Contacted'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    INTERESTED = 'INTERESTED', 'Interested'
    VISIT_SCHEDULED = 'VISIT_SCHEDULED', 'Visit Scheduled'
    CONVERTED = 'CONVERTED', 'Converted'
    NOT_INTERESTED = 'NOT_INTERESTED', 'Not Interested'
    CLOSED = 'CLOSED', 'Closed'
    LOST = 'LOST', 'Lost'
    SPAM = 'SPAM', 'Spam'

class VisitStatusChoices(models.TextChoices):
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    CONFIRMED = 'CONFIRMED', 'Confirmed'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorites'
        unique_together = ('user', 'property')

class SavedSearch(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saved_searches')
    name = models.CharField(max_length=100, null=True, blank=True)
    search_criteria = models.JSONField()
    enable_alerts = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_searches'
        ordering = ['-created_at']

class RecentlyViewed(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recently_viewed')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='viewed_history')
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recently_viewed'
        unique_together = ('user', 'property')
        ordering = ['-viewed_at']

class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preference_profile')
    purpose = models.CharField(max_length=20, choices=ListingPurposeChoices.choices, default=ListingPurposeChoices.BUY)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    locality = models.ForeignKey(Locality, on_delete=models.SET_NULL, null=True, blank=True)
    property_category = models.CharField(max_length=20, choices=PropertyCategoryChoices.choices, default=PropertyCategoryChoices.RESIDENTIAL)
    property_type = models.ForeignKey(PropertyType, on_delete=models.SET_NULL, null=True, blank=True)
    min_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    min_bhk = models.IntegerField(null=True, blank=True, default=1)
    max_bhk = models.IntegerField(null=True, blank=True, default=4)
    min_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    furnishing = models.CharField(max_length=20, choices=FurnishingChoices.choices, null=True, blank=True)
    possession_status = models.CharField(max_length=20, choices=PossessionStatusChoices.choices, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_preferences'

class PropertyPriceHistory(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='price_history')
    previous_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    new_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'property_price_history'
        ordering = ['-changed_at']

class Enquiry(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='enquiries')
    sender_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_enquiries')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'enquiries'
        ordering = ['-created_at']

class Lead(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='leads')
    lead_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leads_as_client')
    owner_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leads_as_agent')
    assigned_agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    status = models.CharField(max_length=30, choices=LeadStatusChoices.choices, default=LeadStatusChoices.NEW)
    notes = models.TextField(null=True, blank=True)
    next_follow_up = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'leads'
        ordering = ['-created_at']

class LeadActivity(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    actor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    activity_type = models.CharField(max_length=50, default='NOTE')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'lead_activities'
        ordering = ['-created_at']

class FollowUpReminder(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='reminders')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminders')
    reminder_date = models.DateTimeField()
    note = models.TextField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'follow_up_reminders'
        ordering = ['reminder_date']

class PropertyVisit(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='visits')
    visitor_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scheduled_visits')
    visit_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=VisitStatusChoices.choices, default=VisitStatusChoices.SCHEDULED)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'property_visits'
        ordering = ['-visit_date']

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    channel = models.CharField(max_length=20, default='IN_APP')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.user.username}"
