from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.core.validators import validate_file_size_5mb, validate_document_file, validate_image_file

class RoleChoices(models.TextChoices):
    CUSTOMER = 'CUSTOMER', 'Customer'
    PARTNER = 'PARTNER', 'Real Estate Partner'
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

class PartnerApprovalStatusChoices(models.TextChoices):
    PENDING = 'PENDING', 'Pending Review'
    UNDER_VERIFICATION = 'UNDER_VERIFICATION', 'Under Verification'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    ADDITIONAL_DOCS_REQUIRED = 'ADDITIONAL_DOCS_REQUIRED', 'Additional Documents Required'

class PartnerDocumentTypeChoices(models.TextChoices):
    GUMASTA = 'GUMASTA', 'Gumasta / Shop and Establishment Registration Certificate'
    MSME = 'MSME', 'MSME Registration Certificate'
    UDYAM = 'UDYAM', 'Udyam Registration Certificate'
    GST = 'GST', 'GST Registration Certificate'
    OTHER = 'OTHER', 'Other Permitted Verification Document'

class User(AbstractUser):
    """
    Custom User model with role-based authorization, Real Estate Partner verification,
    document management, and declaration audit fields.
    """
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=RoleChoices.choices, default=RoleChoices.CUSTOMER)
    status = models.CharField(max_length=20, choices=UserStatusChoices.choices, default=UserStatusChoices.ACTIVE)
    email_verified = models.BooleanField(default=True)
    phone_verified = models.BooleanField(default=True)
    is_identity_verified = models.BooleanField(default=False)
    identity_document = models.FileField(upload_to='verification_docs/', null=True, blank=True, validators=[validate_document_file])
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, validators=[validate_image_file])

    # Real Estate Partner Fields
    agency_name = models.CharField(max_length=255, null=True, blank=True, verbose_name="Business / Agency Name")
    business_address = models.TextField(null=True, blank=True)
    business_state = models.CharField(max_length=100, null=True, blank=True)
    business_city = models.CharField(max_length=100, null=True, blank=True)
    business_locality = models.CharField(max_length=100, null=True, blank=True)
    business_pincode = models.CharField(max_length=20, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)

    # Verification & Approval Status
    partner_approval_status = models.CharField(
        max_length=30,
        choices=PartnerApprovalStatusChoices.choices,
        default=PartnerApprovalStatusChoices.PENDING
    )
    verification_notes = models.TextField(null=True, blank=True)
    partner_rejection_reason = models.TextField(null=True, blank=True)

    # Property Listing Responsibility Declaration Audit Trail
    declaration_accepted = models.BooleanField(default=False)
    declaration_accepted_at = models.DateTimeField(null=True, blank=True)
    declaration_version = models.CharField(max_length=20, default='1.0')

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return f"{full_name or self.username} ({self.get_role_display()})"

    @property
    def is_buyer(self):
        return self.role in [RoleChoices.BUYER, RoleChoices.TENANT_BUYER, RoleChoices.CUSTOMER]

    @property
    def is_tenant(self):
        return self.role in [RoleChoices.TENANT, RoleChoices.TENANT_BUYER]

    @property
    def is_owner(self):
        return self.role == RoleChoices.OWNER

    @property
    def is_agent(self):
        return self.role in [RoleChoices.AGENT, RoleChoices.DEVELOPER, RoleChoices.PARTNER]

    @property
    def is_real_estate_partner(self):
        return self.role in [RoleChoices.PARTNER, RoleChoices.AGENT, RoleChoices.DEVELOPER, RoleChoices.OWNER]

    @property
    def is_approved_partner(self):
        if self.is_admin_role or self.is_superuser or self.is_staff:
            return True
        return self.is_real_estate_partner and self.partner_approval_status == PartnerApprovalStatusChoices.APPROVED

    @property
    def is_customer_account(self):
        return self.role in [RoleChoices.CUSTOMER, RoleChoices.BUYER, RoleChoices.TENANT, RoleChoices.TENANT_BUYER]

    @property
    def is_admin_role(self):
        return self.role in [RoleChoices.ADMIN, RoleChoices.SUPER_ADMIN, RoleChoices.MODERATOR] or self.is_superuser or self.is_staff


class PartnerDocument(models.Model):
    """
    Stores uploaded government and business registration certificates for Real Estate Partner verification.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partner_documents')
    document_type = models.CharField(
        max_length=30,
        choices=PartnerDocumentTypeChoices.choices,
        default=PartnerDocumentTypeChoices.GUMASTA
    )
    file = models.FileField(upload_to='partner_docs/', validators=[validate_document_file])
    original_filename = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.BigIntegerField(default=0)
    verification_status = models.CharField(
        max_length=30,
        choices=PartnerApprovalStatusChoices.choices,
        default=PartnerApprovalStatusChoices.PENDING
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'partner_documents'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.email} - {self.get_document_type_display()}"

