import uuid
import random
import secrets
import hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from apps.core.validators import validate_image_file

class BankCategoryChoices(models.TextChoices):
    PUBLIC_SECTOR = 'PUBLIC_SECTOR', 'Public Sector Bank'
    PRIVATE_SECTOR = 'PRIVATE_SECTOR', 'Private Sector Bank'
    FOREIGN_BANK = 'FOREIGN_BANK', 'Foreign Bank'
    NBFC = 'NBFC', 'Housing Finance Company / NBFC'
    OTHER = 'OTHER', 'Other Financial Institution'

class ProcessingFeeTypeChoices(models.TextChoices):
    PERCENTAGE = 'PERCENTAGE', 'Percentage of Loan Amount'
    FIXED = 'FIXED', 'Fixed Flat Amount'
    RANGE = 'RANGE', 'Fee Range'
    CUSTOM = 'CUSTOM', 'Custom Description'

class BankPartner(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    logo = models.ImageField(upload_to='bank_logos/', null=True, blank=True, validators=[validate_image_file])
    short_description = models.CharField(max_length=255, null=True, blank=True)
    full_description = models.TextField(null=True, blank=True)
    website_url = models.URLField(null=True, blank=True)
    application_url = models.URLField(null=True, blank=True)
    category = models.CharField(max_length=30, choices=BankCategoryChoices.choices, default=BankCategoryChoices.PRIVATE_SECTOR)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Loan Rates & Limits
    min_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Starting interest rate e.g. 8.40")
    max_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_tenure_years = models.IntegerField(default=30)
    min_loan_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    max_loan_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    # Processing Fee
    processing_fee_info = models.CharField(max_length=255, default="Up to 0.50% + GST")
    processing_fee_type = models.CharField(max_length=30, choices=ProcessingFeeTypeChoices.choices, default=ProcessingFeeTypeChoices.CUSTOM)
    processing_fee_description = models.TextField(null=True, blank=True)
    additional_charges = models.TextField(null=True, blank=True)

    # Dynamic Features & Benefits
    benefits = models.JSONField(default=list, blank=True, help_text="Dynamic list of benefits/features")

    # Additional Documentation & Policy Info
    eligibility_info = models.TextField(null=True, blank=True)
    required_documents = models.TextField(null=True, blank=True)
    special_offers = models.TextField(null=True, blank=True)
    disclaimer = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bank_partners'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    @property
    def get_benefits_list(self):
        if isinstance(self.benefits, list) and self.benefits:
            return [str(b).strip() for b in self.benefits if str(b).strip()]
        if isinstance(self.benefits, str) and self.benefits.strip():
            try:
                import json
                parsed = json.loads(self.benefits)
                if isinstance(parsed, list):
                    return [str(b).strip() for b in parsed if str(b).strip()]
            except Exception:
                return [b.strip() for b in self.benefits.split('\n') if b.strip()]
        return []

class BankLoanProduct(models.Model):
    bank = models.ForeignKey(BankPartner, on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    description = models.TextField()
    features = models.TextField(help_text="Bullet points separated by newlines")
    eligibility_criteria = models.TextField(help_text="Eligibility details")
    required_documents = models.TextField(help_text="Required documents list")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'bank_loan_products'

    def __str__(self):
        return f"{self.bank.name} - {self.title}"

class BankLoanEnquiry(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New Enquiry'),
        ('IN_PROGRESS', 'In Progress'),
        ('APPROVED', 'Pre-Approved'),
        ('CLOSED', 'Closed'),
    ]
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    employment_type = models.CharField(max_length=50, choices=[
        ('SALARIED', 'Salaried'),
        ('SELF_EMPLOYED', 'Self-Employed Professional'),
        ('BUSINESS', 'Business Owner'),
    ], default='SALARIED')
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2)
    desired_loan_amount = models.DecimalField(max_digits=14, decimal_places=2)
    preferred_bank = models.ForeignKey(BankPartner, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bank_loan_enquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"Loan Enquiry #{self.id} - {self.name}"

class LoanInquiryStatusChoices(models.TextChoices):
    NEW = 'NEW', 'New'
    CONTACT_PENDING = 'CONTACT_PENDING', 'Contact Pending'
    CONTACTED = 'CONTACTED', 'Contacted'
    DOCUMENTS_REQUESTED = 'DOCUMENTS_REQUESTED', 'Documents Requested'
    UNDER_BANK_EVALUATION = 'UNDER_BANK_EVALUATION', 'Under Bank Evaluation'
    ELIGIBLE = 'ELIGIBLE', 'Eligible'
    NOT_ELIGIBLE = 'NOT_ELIGIBLE', 'Not Eligible'
    LOAN_APPLIED = 'LOAN_APPLIED', 'Loan Applied'
    LOAN_APPROVED = 'LOAN_APPROVED', 'Loan Approved'
    LOAN_REJECTED = 'LOAN_REJECTED', 'Loan Rejected'
    CLOSED = 'CLOSED', 'Closed'

class EmploymentTypeChoices(models.TextChoices):
    SALARIED = 'SALARIED', 'Salaried'
    SELF_EMPLOYED = 'SELF_EMPLOYED', 'Self-Employed Professional'
    BUSINESS = 'BUSINESS', 'Business Owner'

class LoanInquiryLead(models.Model):
    lead_id = models.CharField(max_length=32, unique=True, editable=False, db_index=True)
    full_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=20)
    email_address = models.EmailField()
    employment_type = models.CharField(max_length=50, choices=EmploymentTypeChoices.choices, default=EmploymentTypeChoices.SALARIED)
    net_monthly_income = models.DecimalField(max_digits=14, decimal_places=2)
    desired_loan_amount = models.DecimalField(max_digits=14, decimal_places=2)
    preferred_bank = models.ForeignKey(BankPartner, on_delete=models.SET_NULL, null=True, blank=True, related_name='loan_leads')

    status = models.CharField(
        max_length=30,
        choices=LoanInquiryStatusChoices.choices,
        default=LoanInquiryStatusChoices.NEW,
        db_index=True
    )
    assigned_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_loan_leads'
    )
    admin_notes = models.TextField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loan_inquiry_leads'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.lead_id:
            import uuid
            prefix = "LL"
            timestamp = timezone.now().strftime("%Y%m%d")
            rand_suffix = str(uuid.uuid4().hex[:6]).upper()
            self.lead_id = f"{prefix}-{timestamp}-{rand_suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lead_id} - {self.full_name} ({self.get_status_display()})"

class LoanInquiryNote(models.Model):
    lead = models.ForeignKey(LoanInquiryLead, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loan_inquiry_notes'
        ordering = ['-created_at']

class LoanInquiryStatusHistory(models.Model):
    lead = models.ForeignKey(LoanInquiryLead, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=30, choices=LoanInquiryStatusChoices.choices)
    new_status = models.CharField(max_length=30, choices=LoanInquiryStatusChoices.choices)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loan_inquiry_status_history'
        ordering = ['-created_at']

class RentalAgreementStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending Review'
    PROCESSING = 'PROCESSING', 'Processing & Drafting'
    VERIFICATION = 'VERIFICATION', 'Party Verification'
    COMPLETED = 'COMPLETED', 'Agreement Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class AgreementType(models.TextChoices):
    E_STAMP = 'E_STAMP', 'E-Stamped Rental Agreement'
    NOTARIZED = 'NOTARIZED', 'Notarized Rental Agreement'
    REGISTERED = 'REGISTERED', 'Registered Rent Agreement'

class RentalAgreementRequest(models.Model):
    reference_number = models.CharField(max_length=32, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='rental_agreements')
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    agreement_type = models.CharField(max_length=30, choices=AgreementType.choices, default=AgreementType.E_STAMP)
    property_address = models.TextField()
    city_name = models.CharField(max_length=100, default='Mumbai')
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=12, decimal_places=2)
    tenancy_period_months = models.IntegerField(default=11)
    lock_in_period_months = models.IntegerField(default=1)
    estimated_charge = models.DecimalField(max_digits=10, decimal_places=2, default=499.00)
    status = models.CharField(max_length=30, choices=RentalAgreementStatus.choices, default=RentalAgreementStatus.PENDING)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rental_agreement_requests'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.reference_number:
            prefix = "RA"
            timestamp = timezone.now().strftime("%Y%m%d")
            rand_suffix = str(uuid.uuid4().hex[:6]).upper()
            self.reference_number = f"{prefix}-{timestamp}-{rand_suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rental Request {self.reference_number} - {self.full_name}"

class OTPPurposeChoices(models.TextChoices):
    REGISTER = 'REGISTER', 'Registration Verification'
    LOGIN = 'LOGIN', 'Login Verification'
    PROPERTY_INTEREST = 'PROPERTY_INTEREST', 'Property Interest Verification'

class EmailOTP(models.Model):
    email = models.EmailField(db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='otps')
    otp_hash = models.CharField(max_length=128)
    purpose = models.CharField(max_length=30, choices=OTPPurposeChoices.choices, default=OTPPurposeChoices.REGISTER)
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, null=True, blank=True, related_name='enquiry_otps')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts_count = models.IntegerField(default=0)
    resend_count = models.IntegerField(default=0)
    last_resend_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'email_otps'
        ordering = ['-created_at']

    @classmethod
    def generate_otp(cls, email, purpose=OTPPurposeChoices.REGISTER, user=None, property_obj=None, bypass_cooldown=False):
        email_clean = email.lower().strip()
        now = timezone.now()

        if not bypass_cooldown:
            last_otp = cls.objects.filter(
                email__iexact=email_clean,
                purpose=purpose,
                is_verified=False
            ).order_by('-created_at').first()

            if last_otp and last_otp.last_resend_at and (now - last_otp.last_resend_at).total_seconds() < 60:
                remaining = int(60 - (now - last_otp.last_resend_at).total_seconds())
                raise ValueError(f"Please wait {remaining} seconds before requesting a new OTP code.")

        qs = cls.objects.filter(email__iexact=email_clean, purpose=purpose, is_verified=False)
        if property_obj:
            qs = qs.filter(property=property_obj)
        qs.delete()

        otp_digits = "".join([secrets.choice("0123456789") for _ in range(6)])

        salt = settings.SECRET_KEY[:16]
        otp_hash = hashlib.sha256(f"{otp_digits}{salt}".encode('utf-8')).hexdigest()
        expires_at = now + timedelta(minutes=5)

        otp_obj = cls.objects.create(
            email=email_clean,
            user=user,
            otp_hash=otp_hash,
            purpose=purpose,
            property=property_obj,
            expires_at=expires_at
        )
        return otp_obj, otp_digits

    def verify(self, input_otp, expected_purpose=None, expected_property_id=None):
        now = timezone.now()

        if self.is_verified:
            return False, "This OTP verification code has already been used."

        if expected_purpose and self.purpose != expected_purpose:
            return False, "Invalid OTP purpose mismatch."

        if expected_property_id and (not self.property_id or self.property_id != int(expected_property_id)):
            return False, "OTP code is not valid for this property enquiry."

        if now > self.expires_at:
            return False, "OTP has expired. Please request a new verification code."

        if self.attempts_count >= 5:
            return False, "Maximum verification attempts exceeded. Please request a new OTP."

        self.attempts_count += 1
        salt = settings.SECRET_KEY[:16]
        input_hash = hashlib.sha256(f"{str(input_otp).strip()}{salt}".encode('utf-8')).hexdigest()

        if input_hash == self.otp_hash:
            self.is_verified = True
            self.save(update_fields=['is_verified', 'attempts_count'])
            return True, "OTP verified successfully."
        else:
            self.save(update_fields=['attempts_count'])
            remaining = 5 - self.attempts_count
            if remaining <= 0:
                return False, "Maximum verification attempts exceeded. Please request a new OTP."
            return False, f"Incorrect OTP code. {remaining} attempt(s) remaining."
