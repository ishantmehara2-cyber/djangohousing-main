from django.db import models
from django.conf import settings
from apps.accounts.models import RoleChoices
from apps.properties.models import Property

class PaymentStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SUCCESS = 'SUCCESS', 'Success'
    FAILED = 'FAILED', 'Failed'
    REFUNDED = 'REFUNDED', 'Refunded'

class PromotionTypeChoices(models.TextChoices):
    FEATURED = 'FEATURED', 'Featured Property'
    HOMEPAGE_HIGHLIGHT = 'HOMEPAGE_HIGHLIGHT', 'Homepage Highlight'
    PREMIUM_SEARCH = 'PREMIUM_SEARCH', 'Premium Search Visibility'

class Package(models.Model):
    name = models.CharField(max_length=100)
    target_role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.OWNER)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    validity_days = models.IntegerField(default=30)
    max_listings = models.IntegerField(default=5)
    featured_listings_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'packages'
        ordering = ['price']

    def __str__(self):
        return f"{self.name} (₹{self.price})"

class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'subscriptions'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.user.username} - {self.package.name}"

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    package = models.ForeignKey(Package, on_delete=models.RESTRICT, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatusChoices.choices, default=PaymentStatusChoices.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"TXN-{self.id} | {self.user.username} | ₹{self.amount} ({self.get_status_display()})"

class Invoice(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=100, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-issued_at']

    def __str__(self):
        return f"INV-{self.invoice_number}"

class PropertyPromotion(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='promotions')
    purchaser = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchased_promotions')
    promotion_type = models.CharField(max_length=30, choices=PromotionTypeChoices.choices, default=PromotionTypeChoices.FEATURED)
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='promotions')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'property_promotions'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.property.title} ({self.get_promotion_type_display()})"
