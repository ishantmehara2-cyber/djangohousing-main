from django.urls import path
from apps.services.views import (
    bank_loans_view,
    home_loan_calculator_view,
    rental_agreement_services_view,
    rental_agreement_detail_view,
    admin_rental_agreements_view,
)

app_name = 'services'

urlpatterns = [
    path('bank-loans/', bank_loans_view, name='bank-loans'),
    path('home-loan-calculator/', home_loan_calculator_view, name='loan-calculator'),
    path('rental-agreement/', rental_agreement_services_view, name='rental-agreement'),
    path('rental-agreement/<str:ref_num>/', rental_agreement_detail_view, name='rental-agreement-detail'),
    path('admin/rental-agreements/', admin_rental_agreements_view, name='admin-rental-agreements'),
]
