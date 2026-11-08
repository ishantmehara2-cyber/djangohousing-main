from django.db import models
from django.conf import settings
from apps.properties.models import Property

class ReportStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    RESOLVED = 'RESOLVED', 'Resolved'
    DISMISSED = 'DISMISSED', 'Dismissed'

class ReportReasonChoices(models.TextChoices):
    INCORRECT_INFO = 'INCORRECT_INFO', 'Incorrect Property Information'
    DUPLICATE = 'DUPLICATE', 'Duplicate Listing'
    MISLEADING_PRICE = 'MISLEADING_PRICE', 'Misleading Price'
    FAKE_PROPERTY = 'FAKE_PROPERTY', 'Fake Property'
    INCORRECT_IMAGES = 'INCORRECT_IMAGES', 'Incorrect Images'
    SUSPICIOUS_CONTACT = 'SUSPICIOUS_CONTACT', 'Suspicious Contact Details'
    OTHER = 'OTHER', 'Other'

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=100)
    entity = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100, null=True, blank=True)
    payload = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} on {self.entity} by {self.user}"

class PropertyVerification(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='verifications')
    verifier_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verified_properties')
    notes = models.TextField(null=True, blank=True)
    verified_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'property_verifications'

class Report(models.Model):
    reporter_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='filed_reports')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reports')
    reason_category = models.CharField(max_length=50, choices=ReportReasonChoices.choices, default=ReportReasonChoices.OTHER)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=ReportStatusChoices.choices, default=ReportStatusChoices.PENDING)
    investigation_notes = models.TextField(null=True, blank=True)
    resolved_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports')
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id} on {self.property.title} - {self.get_status_display()}"
