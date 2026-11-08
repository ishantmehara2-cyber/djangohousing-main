from django import forms
from apps.services.models import BankLoanEnquiry, RentalAgreementRequest, AgreementType

class BankLoanEnquiryForm(forms.ModelForm):
    class Meta:
        model = BankLoanEnquiry
        fields = ['name', 'email', 'phone', 'employment_type', 'monthly_income', 'desired_loan_amount', 'preferred_bank']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-red-500 text-sm', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-red-500 text-sm', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-red-500 text-sm', 'placeholder': 'Mobile Number'}),
            'employment_type': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-red-500 text-sm'}),
            'monthly_income': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-red-500 text-sm', 'placeholder': 'Monthly Net Income (₹)'}),
            'desired_loan_amount': forms.NumberInput(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-red-500 text-sm', 'placeholder': 'Desired Loan Amount (₹)'}),
            'preferred_bank': forms.Select(attrs={'class': 'w-full px-4 py-2.5 border rounded-xl focus:ring-2 focus:ring-red-500 text-sm'}),
        }

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
