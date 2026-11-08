import math
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.permissions import admin_required
from apps.services.models import BankPartner, BankLoanProduct, BankLoanEnquiry, RentalAgreementRequest, RentalAgreementStatus, AgreementType
from apps.services.forms import BankLoanEnquiryForm, HomeLoanCalculatorForm, RentalAgreementRequestForm

def bank_loans_view(request):
    """
    Renders the Bank Loan Services page with loan overview, eligibility guidelines,
    required documents, bank options, FAQs, and an enquiry submission form.
    """
    banks = BankPartner.objects.filter(is_active=True).prefetch_related('products')

    # Default bank partner fallback if none in database yet
    default_banks = [
        {
            'name': 'HDFC Bank',
            'min_interest_rate': 8.50,
            'max_tenure_years': 30,
            'processing_fee_info': '0.50% of loan amount + GST',
            'features': ['Instant digital sanction', 'Special rates for women borrowers', 'Zero prepayment penalty']
        },
        {
            'name': 'State Bank of India (SBI)',
            'min_interest_rate': 8.40,
            'max_tenure_years': 30,
            'processing_fee_info': 'Nil to 0.35% + GST',
            'features': ['Concession on CIBIL score 750+', 'Overdraft facility available', 'No hidden charges']
        },
        {
            'name': 'ICICI Bank',
            'min_interest_rate': 8.60,
            'max_tenure_years': 30,
            'processing_fee_info': '0.50% or ₹3,000 + GST',
            'features': ['Pre-approved home loans', 'Flexible repayment options', 'Balance transfer benefits']
        },
        {
            'name': 'Axis Bank',
            'min_interest_rate': 8.55,
            'max_tenure_years': 30,
            'processing_fee_info': 'Up to 1% or ₹10,000',
            'features': ['12 EMI waiver on timely payments', '100% digital process', 'Customized top-up loans']
        }
    ]

    if request.method == 'POST':
        form = BankLoanEnquiryForm(request.POST)
        if form.is_valid():
            enquiry = form.save()
            messages.success(request, f"Thank you {enquiry.name}! Your home loan enquiry has been registered. Our financial advisor will contact you within 24 hours.")
            return redirect('services:bank-loans')
        else:
            messages.error(request, "Please correct the errors in the loan enquiry form below.")
    else:
        form = BankLoanEnquiryForm()

    context = {
        'banks': banks,
        'default_banks': default_banks,
        'form': form,
    }
    return render(request, 'services/bank_loans.html', context)


def home_loan_calculator_view(request):
    """
    Home Loan Eligibility & EMI Calculator.
    Mathematically computes maximum eligible loan amount and EMI based on FOIR (Fixed Obligation to Income Ratio).
    """
    form = HomeLoanCalculatorForm(request.GET if request.GET else None)

    income = 75000.0
    existing_emi = 0.0
    tenure_years = 20
    annual_rate = 8.50
    foir_percent = 50.0

    if request.GET and form.is_valid():
        income = float(form.cleaned_data['monthly_income'])
        existing_emi = float(form.cleaned_data.get('existing_emi') or 0.0)
        tenure_years = int(form.cleaned_data['tenure_years'])
        annual_rate = float(form.cleaned_data['interest_rate'])
        foir_percent = float(form.cleaned_data.get('foir_percentage') or 50.0)
    elif request.GET:
        try:
            income = float(request.GET.get('monthly_income', 75000))
            existing_emi = float(request.GET.get('existing_emi', 0))
            tenure_years = int(request.GET.get('tenure_years', 20))
            annual_rate = float(request.GET.get('interest_rate', 8.5))
        except (ValueError, TypeError):
            pass

    # 1. Fixed Obligation to Income Ratio (FOIR) capacity
    max_total_emi_capacity = income * (foir_percent / 100.0)
    max_available_emi = max(0.0, max_total_emi_capacity - existing_emi)

    # 2. Monthly interest rate & total months
    r = (annual_rate / 100.0) / 12.0
    n = tenure_years * 12

    # 3. Calculate Maximum Loan Amount: Present Value PV = EMI * [(1+r)^n - 1] / [r * (1+r)^n]
    if max_available_emi > 0 and r > 0 and n > 0:
        discount_factor = ((1 + r) ** n - 1) / (r * ((1 + r) ** n))
        max_loan_amount = max_available_emi * discount_factor

        # Standard EMI for the calculated max loan
        estimated_emi = max_available_emi
        total_repayment = estimated_emi * n
        total_interest = total_repayment - max_loan_amount
    else:
        max_loan_amount = 0.0
        estimated_emi = 0.0
        total_repayment = 0.0
        total_interest = 0.0

    result = {
        'monthly_income': income,
        'existing_emi': existing_emi,
        'foir_percent': foir_percent,
        'max_total_emi_capacity': round(max_total_emi_capacity, 2),
        'max_available_emi': round(max_available_emi, 2),
        'max_loan_amount': round(max_loan_amount, 2),
        'estimated_emi': round(estimated_emi, 2),
        'total_repayment': round(total_repayment, 2),
        'total_interest': round(total_interest, 2),
        'tenure_years': tenure_years,
        'annual_rate': annual_rate,
        'is_eligible': max_available_emi > 0 and max_loan_amount > 0,
    }

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'success': True, 'result': result})

    context = {
        'form': form,
        'result': result,
    }
    return render(request, 'services/loan_calculator.html', context)


def rental_agreement_services_view(request):
    """
    Rental Agreement Services page with legal process workflow, required documents,
    pricing options, and request submission form.
    """
    if request.method == 'POST':
        form = RentalAgreementRequestForm(request.POST)
        if form.is_valid():
            req_obj = form.save(commit=False)
            if request.user.is_authenticated:
                req_obj.user = request.user

            # Set transparent service charges based on agreement type
            if req_obj.agreement_type == AgreementType.REGISTERED:
                req_obj.estimated_charge = 1999.00
            elif req_obj.agreement_type == AgreementType.NOTARIZED:
                req_obj.estimated_charge = 799.00
            else:
                req_obj.estimated_charge = 499.00

            req_obj.save()
            messages.success(
                request,
                f"Your rental agreement request has been submitted successfully! "
                f"Reference Number: {req_obj.reference_number}. "
                f"Our legal executive will get in touch with you shortly."
            )
            return redirect('services:rental-agreement-detail', ref_num=req_obj.reference_number)
        else:
            messages.error(request, "Please check the form inputs and try again.")
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'full_name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'phone': getattr(request.user, 'phone', '') or '',
            }
        form = RentalAgreementRequestForm(initial=initial_data)

    context = {
        'form': form,
    }
    return render(request, 'services/rental_agreement.html', context)


def rental_agreement_detail_view(request, ref_num):
    """
    View status of a submitted rental agreement request by reference number.
    """
    agreement_req = get_object_or_404(RentalAgreementRequest, reference_number=ref_num)
    context = {
        'agreement': agreement_req,
    }
    return render(request, 'services/rental_agreement_detail.html', context)


@login_required
@admin_required
def admin_rental_agreements_view(request):
    """
    Admin portal view to review and manage submitted rental agreement requests.
    """
    status_filter = request.GET.get('status', '')
    agreements = RentalAgreementRequest.objects.all()
    if status_filter:
        agreements = agreements.filter(status=status_filter)

    context = {
        'agreements': agreements,
        'status_choices': RentalAgreementStatus.choices,
        'selected_status': status_filter,
    }
    return render(request, 'services/admin_rental_agreements.html', context)
