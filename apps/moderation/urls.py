from django.urls import path
from apps.moderation.views import (
    admin_dashboard_overview_view,
    admin_pending_properties_view,
    admin_approve_property_view,
    admin_reject_property_view,
    admin_all_properties_view,
    admin_users_view,
    admin_toggle_user_status_view,
    admin_enquiries_view,
    admin_visits_view,
    admin_reports_view,
    admin_audit_logs_view,
    admin_resolve_report_view,
    admin_property_fields_management_view,
    report_property_view
)

app_name = 'moderation'

urlpatterns = [
    path('', admin_dashboard_overview_view, name='dashboard'),
    path('properties/pending/', admin_pending_properties_view, name='pending-properties'),
    path('property/<int:pk>/approve/', admin_approve_property_view, name='approve-property'),
    path('property/<int:pk>/reject/', admin_reject_property_view, name='reject-property'),
    path('properties/', admin_all_properties_view, name='all-properties'),
    path('users/', admin_users_view, name='users'),
    path('user/<int:pk>/toggle/', admin_toggle_user_status_view, name='toggle-user'),
    path('enquiries/', admin_enquiries_view, name='enquiries'),
    path('visits/', admin_visits_view, name='visits'),
    path('reports/', admin_reports_view, name='reports'),
    path('reports/<int:pk>/resolve/', admin_resolve_report_view, name='resolve-report'),
    path('audit-logs/', admin_audit_logs_view, name='audit-logs'),
    path('property-fields/', admin_property_fields_management_view, name='property-fields'),
    path('property/<slug:slug>/report/', report_property_view, name='report-property'),
]
