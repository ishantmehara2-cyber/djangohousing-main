from django.db import models
from django.conf import settings

class CMSContent(models.Model):
    slug = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    meta_title = models.CharField(max_length=255, null=True, blank=True)
    meta_desc = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cms_contents'

    def __str__(self):
        return self.title

class FeatureFlag(models.Model):
    key = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    is_enabled = models.BooleanField(default=False)

    class Meta:
        db_table = 'feature_flags'

    def __str__(self):
        return f"{self.key} ({'ON' if self.is_enabled else 'OFF'})"

class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()

    class Meta:
        db_table = 'system_settings'

    def __str__(self):
        return f"{self.key} = {self.value}"

class FAQCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        db_table = 'faq_categories'
        ordering = ['display_order', 'name']
        verbose_name_plural = 'FAQ Categories'

    def __str__(self):
        return self.name

class FAQItem(models.Model):
    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255)
    answer = models.TextField()
    display_order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        db_table = 'faq_items'
        ordering = ['display_order', 'id']
        verbose_name_plural = 'FAQ Items'

    def __str__(self):
        return self.question

class TicketCategoryChoices(models.TextChoices):
    ACCOUNT = 'ACCOUNT', 'Account and Login'
    LISTING = 'LISTING', 'Property Listing'
    ENQUIRY = 'ENQUIRY', 'Property Enquiries & Visits'
    PAYMENT = 'PAYMENT', 'Payments and Subscriptions'
    TECHNICAL = 'TECHNICAL', 'Technical Issues'
    OTHER = 'OTHER', 'Other'

class TicketStatusChoices(models.TextChoices):
    OPEN = 'OPEN', 'Open'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    WAITING_FOR_USER = 'WAITING_FOR_USER', 'Waiting for User'
    RESOLVED = 'RESOLVED', 'Resolved'
    CLOSED = 'CLOSED', 'Closed'

class TicketPriorityChoices(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    URGENT = 'URGENT', 'Urgent'

class SupportTicket(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='support_tickets')
    ticket_id = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=30, choices=TicketCategoryChoices.choices, default=TicketCategoryChoices.OTHER)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=30, choices=TicketStatusChoices.choices, default=TicketStatusChoices.OPEN)
    priority = models.CharField(max_length=20, choices=TicketPriorityChoices.choices, default=TicketPriorityChoices.MEDIUM)
    attachment = models.FileField(upload_to='support_attachments/', null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'support_tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"TICKET-{self.ticket_id} ({self.get_status_display()})"

class TicketMessage(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ticket_messages')
    message = models.TextField()
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ticket_messages'
        ordering = ['created_at']
