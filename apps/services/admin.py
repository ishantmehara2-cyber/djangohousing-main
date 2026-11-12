from django.contrib import admin
from apps.services.models import (
    BankPartner,
    BankLoanProduct,
    BankLoanEnquiry,
    RentalAgreementRequest,
    EmailOTP,
    LoanInquiryLead,
    LoanInquiryNote,
    LoanInquiryStatusHistory
)

@admin.register(LoanInquiryLead)
class LoanInquiryLeadAdmin(admin.ModelAdmin):
    list_display = ('lead_id', 'full_name', 'mobile_number', 'email_address', 'employment_type', 'net_monthly_income', 'desired_loan_amount', 'preferred_bank', 'status', 'created_at')
    list_filter = ('status', 'employment_type', 'preferred_bank', 'is_deleted')
    search_fields = ('lead_id', 'full_name', 'email_address', 'mobile_number')
    ordering = ('-created_at',)

@admin.register(LoanInquiryNote)
class LoanInquiryNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead', 'author', 'created_at')
    search_fields = ('lead__lead_id', 'lead__full_name', 'note_text')

@admin.register(LoanInquiryStatusHistory)
class LoanInquiryStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead', 'old_status', 'new_status', 'updated_by', 'created_at')
    search_fields = ('lead__lead_id', 'lead__full_name')

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
