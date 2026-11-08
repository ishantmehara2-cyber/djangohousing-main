from django.contrib import admin
from apps.services.models import BankPartner, BankLoanProduct, BankLoanEnquiry, RentalAgreementRequest, EmailOTP

@admin.register(BankPartner)
class BankPartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_interest_rate', 'max_tenure_years', 'is_active', 'display_order')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(BankLoanProduct)
class BankLoanProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'bank', 'is_active')
    list_filter = ('bank', 'is_active')
    search_fields = ('title', 'bank__name')

@admin.register(BankLoanEnquiry)
class BankLoanEnquiryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'desired_loan_amount', 'status', 'created_at')
    list_filter = ('status', 'employment_type')
    search_fields = ('name', 'email', 'phone')

@admin.register(RentalAgreementRequest)
class RentalAgreementRequestAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'full_name', 'email', 'phone', 'agreement_type', 'status', 'created_at')
    list_filter = ('status', 'agreement_type')
    search_fields = ('reference_number', 'full_name', 'email', 'phone', 'property_address')

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at', 'expires_at', 'attempts_count', 'resend_count', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('email',)
