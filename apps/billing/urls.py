from django.urls import path
from apps.billing.views import (
    pricing_view,
    checkout_view,
    verify_payment_view,
    promote_property_view,
    verify_promotion_view,
    user_billing_dashboard_view,
    admin_revenue_dashboard_view
)

app_name = 'billing'

urlpatterns = [
    path('pricing/', pricing_view, name='pricing'),
    path('packages/', pricing_view, name='packages-alias'),
    path('billing/checkout/<int:package_id>/', checkout_view, name='checkout'),
    path('billing/verify/', verify_payment_view, name='verify-payment'),
    path('billing/promote/<slug:slug>/', promote_property_view, name='promote-property'),
    path('billing/verify-promotion/', verify_promotion_view, name='verify-promotion'),
    path('dashboard/billing/', user_billing_dashboard_view, name='billing-dashboard'),
    path('admin-panel/revenue/', admin_revenue_dashboard_view, name='admin-revenue'),
]
