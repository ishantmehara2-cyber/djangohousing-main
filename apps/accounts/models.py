from django.db import models
from django.contrib.auth.models import AbstractUser

class RoleChoices(models.TextChoices):
    BUYER = 'BUYER', 'Buyer'
    TENANT = 'TENANT', 'Tenant'
    OWNER = 'OWNER', 'Property Owner'
    AGENT = 'AGENT', 'Real Estate Agent / Broker'
    ADMIN = 'ADMIN', 'Admin'
    TENANT_BUYER = 'TENANT_BUYER', 'Tenant / Buyer (Legacy)'
    DEVELOPER = 'DEVELOPER', 'Property Developer'
    MODERATOR = 'MODERATOR', 'Moderator'
    SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'

class UserStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    ACTIVE = 'ACTIVE', 'Active'
    SUSPENDED = 'SUSPENDED', 'Suspended'
    DELETED = 'DELETED', 'Deleted'

class User(AbstractUser):
    """
    Custom User model with role-based authorization, phone number, and account verification flags.
    """
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.BUYER)
    status = models.CharField(max_length=20, choices=UserStatusChoices.choices, default=UserStatusChoices.ACTIVE)
    email_verified = models.BooleanField(default=True)
    phone_verified = models.BooleanField(default=True)
    is_identity_verified = models.BooleanField(default=False)
    identity_document = models.FileField(upload_to='verification_docs/', null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    agency_name = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return f"{full_name or self.username} ({self.get_role_display()})"

    @property
    def is_buyer(self):
        return self.role in [RoleChoices.BUYER, RoleChoices.TENANT_BUYER]

    @property
    def is_tenant(self):
        return self.role in [RoleChoices.TENANT, RoleChoices.TENANT_BUYER]

    @property
    def is_owner(self):
        return self.role == RoleChoices.OWNER

    @property
    def is_agent(self):
        return self.role in [RoleChoices.AGENT, RoleChoices.DEVELOPER]

    @property
    def is_admin_role(self):
        return self.role in [RoleChoices.ADMIN, RoleChoices.SUPER_ADMIN, RoleChoices.MODERATOR] or self.is_superuser or self.is_staff
