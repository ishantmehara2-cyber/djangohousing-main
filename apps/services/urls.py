from django.urls import path
from apps.services.views import (
    bank_loans_view,
    home_loan_calculator_view,
    rental_agreement_services_view,
    rental_agreement_detail_view,
    admin_rental_agreements_view,
    admin_bank_management_view,
    admin_add_bank_view,
    admin_edit_bank_view,
    admin_toggle_bank_active_view,
    admin_delete_bank_view,
    admin_loan_inquiries_view,
    admin_loan_inquiry_detail_view,
    admin_delete_loan_inquiry_view,
    admin_export_loan_inquiries_csv_view,
)
from apps.services.api_views import (
    api_public_banks_list,
    api_public_bank_detail,
    api_admin_banks_list,
    api_admin_bank_create,
    api_admin_bank_detail,
    api_public_loan_inquiry_create,
    api_admin_loan_inquiries_list,
    api_admin_loan_inquiry_detail,
    api_admin_loan_inquiry_add_note,
    api_admin_loan_inquiry_history,
)

app_name = 'services'

urlpatterns = [
    # Public Web Pages
    path('bank-loans/', bank_loans_view, name='bank-loans'),
    path('home-loan-calculator/', home_loan_calculator_view, name='loan-calculator'),
    path('rental-agreement/', rental_agreement_services_view, name='rental-agreement'),
    path('rental-agreement/<str:ref_num>/', rental_agreement_detail_view, name='rental-agreement-detail'),

    # Admin Portal Views
    path('admin/rental-agreements/', admin_rental_agreements_view, name='admin-rental-agreements'),
    path('admin/banks/', admin_bank_management_view, name='admin-bank-management'),
    path('admin/banks/add/', admin_add_bank_view, name='admin-add-bank'),
    path('admin/banks/<int:pk>/edit/', admin_edit_bank_view, name='admin-edit-bank'),
    path('admin/banks/<int:pk>/toggle-active/', admin_toggle_bank_active_view, name='admin-toggle-bank-active'),
    path('admin/banks/<int:pk>/delete/', admin_delete_bank_view, name='admin-delete-bank'),

    # Admin Loan Inquiry Leads Views (MODULE 3, 4, 5, 6, 7)
    path('admin/loan-inquiries/', admin_loan_inquiries_view, name='admin-loan-inquiries'),
    path('admin/loan-inquiries/<int:lead_id>/', admin_loan_inquiry_detail_view, name='admin-loan-inquiry-detail'),
    path('admin/loan-inquiries/<int:pk>/delete/', admin_delete_loan_inquiry_view, name='admin-delete-loan-inquiry'),
    path('admin/loan-inquiries/export/', admin_export_loan_inquiries_csv_view, name='admin-export-loan-inquiries-csv'),

    # Public REST APIs
    path('api/banks/', api_public_banks_list, name='api-public-banks-list'),
    path('api/banks/<int:pk>/', api_public_bank_detail, name='api-public-bank-detail'),
    path('api/loan-inquiries/', api_public_loan_inquiry_create, name='api-public-loan-inquiry-create'),

    # Admin REST APIs
    path('api/admin/banks/', api_admin_banks_list, name='api-admin-banks-list'),
    path('api/admin/banks/create/', api_admin_bank_create, name='api-admin-bank-create'),
    path('api/admin/banks/<int:pk>/', api_admin_bank_detail, name='api-admin-bank-detail'),

    path('api/admin/loan-inquiries/', api_admin_loan_inquiries_list, name='api-admin-loan-inquiries-list'),
    path('api/admin/loan-inquiries/<int:pk>/', api_admin_loan_inquiry_detail, name='api-admin-loan-inquiry-detail'),
    path('api/admin/loan-inquiries/<int:pk>/notes/', api_admin_loan_inquiry_add_note, name='api-admin-loan-inquiry-add-note'),
    path('api/admin/loan-inquiries/<int:pk>/history/', api_admin_loan_inquiry_history, name='api-admin-loan-inquiry-history'),
]
