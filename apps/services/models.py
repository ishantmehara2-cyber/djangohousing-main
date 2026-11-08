import uuid
import random
import secrets
import hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class BankPartner(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    logo = models.ImageField(upload_to='bank_logos/', null=True, blank=True)
    min_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Starting interest rate e.g. 8.40")
    max_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_tenure_years = models.IntegerField(default=30)
    processing_fee_info = models.CharField(max_length=255, default="Up to 0.50% + GST")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bank_partners'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

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

        # Resend cooldown check (60 seconds)
        if not bypass_cooldown:
            last_otp = cls.objects.filter(
                email__iexact=email_clean,
                purpose=purpose,
                is_verified=False
            ).order_by('-created_at').first()

            if last_otp and last_otp.last_resend_at and (now - last_otp.last_resend_at).total_seconds() < 60:
                remaining = int(60 - (now - last_otp.last_resend_at).total_seconds())
                raise ValueError(f"Please wait {remaining} seconds before requesting a new OTP code.")

        # Invalidate unverified OTPs for same email & purpose (& property if applicable)
        qs = cls.objects.filter(email__iexact=email_clean, purpose=purpose, is_verified=False)
        if property_obj:
            qs = qs.filter(property=property_obj)
        qs.delete()

        # Cryptographically secure 6-digit OTP
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
