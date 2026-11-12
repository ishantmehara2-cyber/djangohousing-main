from django import forms
from apps.services.models import (
    BankPartner,
    BankLoanEnquiry,
    RentalAgreementRequest,
    AgreementType,
    BankCategoryChoices,
    ProcessingFeeTypeChoices,
    LoanInquiryLead,
    EmploymentTypeChoices
)

class LoanInquiryLeadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferred_bank'].queryset = BankPartner.objects.filter(is_active=True)
        self.fields['preferred_bank'].required = False

    class Meta:
        model = LoanInquiryLead
        fields = [
            'full_name', 'mobile_number', 'email_address',
            'employment_type', 'net_monthly_income',
            'desired_loan_amount', 'preferred_bank'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'w-full px-4 py-3 bg-white text-gray-900 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-primary outline-none text-xs font-bold placeholder-gray-400 shadow-sm', 'placeholder': 'Full Name'}),
            'email_address': forms.EmailInput(attrs={'class': 'w-full px-4 py-3 bg-white text-gray-900 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-primary outline-none text-xs font-bold placeholder-gray-400 shadow-sm', 'placeholder': 'Email Address'}),
            'mobile_number': forms.TextInput(attrs={'class': 'w-full px-4 py-3 bg-white text-gray-900 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-primary outline-none text-xs font-bold placeholder-gray-400 shadow-sm', 'placeholder': 'Mobile Number'}),
            'employment_type': forms.Select(attrs={'class': 'w-full px-4 py-3 bg-white text-gray-900 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-primary outline-none text-xs font-bold shadow-sm'}),
            'net_monthly_income': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 bg-white text-gray-900 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-primary outline-none text-xs font-bold placeholder-gray-400 shadow-sm', 'placeholder': 'Monthly Net Income (₹)'}),
            'desired_loan_amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-3 bg-white text-gray-900 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-primary outline-none text-xs font-bold placeholder-gray-400 shadow-sm', 'placeholder': 'Desired Loan Amount (₹)'}),
            'preferred_bank': forms.Select(attrs={'class': 'w-full px-4 py-3 bg-white text-gray-900 border border-gray-200 rounded-xl focus:ring-2 focus:ring-brand-primary outline-none text-xs font-bold shadow-sm'}),
        }

class BankLoanEnquiryForm(LoanInquiryLeadForm):
    pass

class HomeLoanCalculatorForm(forms.Form):
    monthly_income = forms.DecimalField(
        min_value=10000,
        max_value=10000000,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-primary text-sm font-semibold',
            'placeholder': 'e.g. 75000'
        })
    )
    existing_emi = forms.DecimalField(
        min_value=0,
        max_value=5000000,
        max_digits=12,
        decimal_places=2,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-primary text-sm font-semibold',
            'placeholder': 'e.g. 15000 (0 if none)'
        })
    )
    tenure_years = forms.IntegerField(
        min_value=1,
        max_value=30,
        initial=20,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-primary text-sm font-semibold',
            'placeholder': 'e.g. 20'
        })
    )
    interest_rate = forms.DecimalField(
        min_value=5.0,
        max_value=25.0,
        max_digits=5,
        decimal_places=2,
        initial=8.50,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-primary text-sm font-semibold',
            'placeholder': 'e.g. 8.5'
        })
    )
    foir_percentage = forms.DecimalField(
        min_value=30.0,
        max_value=70.0,
        max_digits=5,
        decimal_places=2,
        initial=50.0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-brand-primary text-sm font-semibold',
            'placeholder': '50'
        })
    )

class RentalAgreementRequestForm(forms.ModelForm):
    class Meta:
        model = RentalAgreementRequest
        fields = [
            'full_name', 'email', 'phone', 'agreement_type',
            'property_address', 'city_name', 'monthly_rent',
            'security_deposit', 'tenancy_period_months', 'lock_in_period_months', 'notes'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary', 'placeholder': 'Full Legal Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary', 'placeholder': 'Mobile Number'}),
            'agreement_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary'}),
            'property_address': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary', 'rows': 3, 'placeholder': 'Complete Property Address'}),
            'city_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary', 'placeholder': 'City'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary', 'placeholder': 'Monthly Rent (₹)'}),
            'security_deposit': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary', 'placeholder': 'Security Deposit (₹)'}),
            'tenancy_period_months': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary', 'placeholder': '11'}),
            'lock_in_period_months': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary', 'placeholder': '1'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-primary', 'rows': 2, 'placeholder': 'Additional Requirements / Special Clauses'}),
        }

class BankPartnerForm(forms.ModelForm):
    benefits_raw = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2.5 border border-gray-300 rounded-xl text-xs font-semibold focus:ring-2 focus:ring-brand-primary',
            'rows': 4,
            'placeholder': 'Enter benefits/features (one per line):\nInstant digital sanction\nSpecial rates for women borrowers\nZero prepayment penalty'
        }),
        help_text="Enter benefits/features, one item per line."
    )

    class Meta:
        model = BankPartner
        fields = [
            'name', 'slug', 'logo', 'short_description', 'full_description',
            'website_url', 'application_url', 'category', 'display_order', 'is_active',
            'min_interest_rate', 'max_interest_rate', 'max_tenure_years',
            'min_loan_amount', 'max_loan_amount', 'processing_fee_info',
            'processing_fee_type', 'processing_fee_description', 'additional_charges',
            'eligibility_info', 'required_documents', 'special_offers', 'disclaimer'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary'}),
            'slug': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'placeholder': 'e.g. hdfc-bank'}),
            'short_description': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary'}),
            'full_description': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'rows': 3}),
            'website_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'placeholder': 'https://...'}),
            'application_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'placeholder': 'https://...'}),
            'category': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary'}),
            'display_order': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary'}),
            'min_interest_rate': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'step': '0.01'}),
            'max_interest_rate': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'step': '0.01'}),
            'max_tenure_years': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary'}),
            'min_loan_amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary'}),
            'max_loan_amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary'}),
            'processing_fee_info': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary'}),
            'processing_fee_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary'}),
            'processing_fee_description': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'rows': 2}),
            'additional_charges': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'rows': 2}),
            'eligibility_info': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'rows': 2}),
            'required_documents': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'rows': 2}),
            'special_offers': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'rows': 2}),
            'disclaimer': forms.Textarea(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl text-xs font-bold focus:ring-2 focus:ring-brand-primary', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False
        self.fields['processing_fee_type'].required = False
        if self.instance and self.instance.pk:
            benefits_list = self.instance.get_benefits_list
            self.fields['benefits_raw'].initial = "\n".join(benefits_list)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('slug') and cleaned_data.get('name'):
            from django.utils.text import slugify
            cleaned_data['slug'] = slugify(cleaned_data['name'])
        if not cleaned_data.get('processing_fee_type'):
            cleaned_data['processing_fee_type'] = ProcessingFeeTypeChoices.CUSTOM
        return cleaned_data

    def clean_benefits_raw(self):
        raw = self.cleaned_data.get('benefits_raw', '')
        lines = [b.strip() for b in raw.split('\n') if b.strip()]
        return lines

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo and hasattr(logo, 'size'):
            from apps.core.validators import validate_image_file
            validate_image_file(logo)
        return logo

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.benefits = self.cleaned_data.get('benefits_raw', [])
        if commit:
            instance.save()
        return instance
