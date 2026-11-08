from django.urls import path
from django.contrib.auth import views as auth_views
from apps.accounts.views import (
    register_view,
    verify_otp_view,
    verify_login_otp_view,
    resend_otp_view,
    login_view,
    logout_view,
    dashboard_view,
    buyer_dashboard_view,
    tenant_dashboard_view,
    owner_dashboard_view,
    agent_dashboard_view,
    admin_dashboard_view,
    profile_view,
    edit_profile_view,
    update_lead_status_view,
    api_register_view,
    api_verify_registration_otp_view,
    api_login_view,
    api_verify_login_otp_view,
    api_resend_otp_view,
)
from apps.accounts.forms import CustomPasswordResetForm, CustomSetPasswordForm

app_name = 'accounts'

urlpatterns = [
    # Auth Web Pages
    path('auth/register/', register_view, name='register'),
    path('auth/verify-otp/', verify_otp_view, name='verify_otp'),
    path('auth/login/', login_view, name='login'),
    path('auth/verify-login-otp/', verify_login_otp_view, name='verify_login_otp'),
    path('auth/resend-otp/', resend_otp_view, name='resend_otp'),
    path('auth/logout/', logout_view, name='logout'),

    # REST APIs
    path('api/auth/register/', api_register_view, name='api_register'),
    path('api/auth/verify-registration-otp/', api_verify_registration_otp_view, name='api_verify_registration_otp'),
    path('api/auth/login/', api_login_view, name='api_login'),
    path('api/auth/verify-login-otp/', api_verify_login_otp_view, name='api_verify_login_otp'),
    path('api/auth/resend-otp/', api_resend_otp_view, name='api_resend_otp'),

    # Profile
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile_view, name='edit_profile'),

    # Dashboards
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/buyer/', buyer_dashboard_view, name='buyer_dashboard'),
    path('dashboard/tenant/', tenant_dashboard_view, name='tenant_dashboard'),
    path('dashboard/owner/', owner_dashboard_view, name='owner_dashboard'),
    path('dashboard/agent/', agent_dashboard_view, name='agent_dashboard'),
    path('dashboard/admin/', admin_dashboard_view, name='admin_dashboard'),

    # Lead management
    path('leads/<int:lead_id>/update-status/', update_lead_status_view, name='update_lead_status'),

    # Password Reset Workflow
    path('auth/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset_form.html',
        email_template_name='auth/password_reset_email.html',
        subject_template_name='auth/password_reset_subject.txt',
        form_class=CustomPasswordResetForm,
        success_url='/auth/password-reset/done/'
    ), name='password_reset'),

    path('auth/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='auth/password_reset_done.html'
    ), name='password_reset_done'),

    path('auth/password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='auth/password_reset_confirm.html',
        form_class=CustomSetPasswordForm,
        success_url='/auth/password-reset-complete/'
    ), name='password_reset_complete_confirm'),

    path('auth/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='auth/password_reset_complete.html'
    ), name='password_reset_complete'),
]
