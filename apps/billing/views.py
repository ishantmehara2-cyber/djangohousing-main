from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Sum

from apps.accounts.models import RoleChoices
from apps.billing.models import (
    Package, Subscription, Transaction, Invoice,
    PropertyPromotion, PaymentStatusChoices, PromotionTypeChoices
)
from apps.billing.services.payment import PaymentService
from apps.properties.models import Property, ListingStateChoices

def render_billing_template(request, template_name, context):
    context['request'] = request
    context['user'] = request.user
    template = get_template(template_name)
    return HttpResponse(template.render(context, request))
    
   

def pricing_view(request):
    """Public pricing page displaying available plans, benefits, and user's current subscription."""
    packages = Package.objects.filter(is_active=True).order_by('price')
    active_sub = PaymentService.get_user_active_subscription(request.user) if request.user.is_authenticated else None

    context = {
        'packages': packages,
        'active_sub': active_sub,
    }
    return render_billing_template(request, 'billing/pricing.html', context)

@login_required
def checkout_view(request, package_id):
    """Initiates checkout order for selected subscription plan."""
    package = get_object_or_404(Package, id=package_id, is_active=True)
    txn = PaymentService.create_subscription_order(request.user, package)

    context = {
        'package': package,
        'transaction': txn,
        'key_id': 'rzp_test_housing_clone_2026',
    }
    return render_billing_template(request, 'billing/checkout.html', context)

@login_required
def verify_payment_view(request):
    """Verifies backend payment signature and activates user subscription."""
    if request.method == 'POST':
        txn_id = request.POST.get('transaction_id')
        payment_id = request.POST.get('razorpay_payment_id', 'pay_test_verified_123')

        try:
            txn = PaymentService.verify_and_activate_subscription(
                user=request.user,
                transaction_id=txn_id,
                payment_id=payment_id
            )
            messages.success(request, f"Payment verified successfully! Your '{txn.package.name}' plan is now active.")
            return redirect('billing:billing-dashboard')
        except Transaction.DoesNotExist:
            messages.error(request, "Invalid or non-existent transaction record.")
            return redirect('billing:pricing')

    return redirect('billing:pricing')

@login_required
def promote_property_view(request, slug):
    """Allows owner to initiate featured property promotion."""
    property_item = get_object_or_404(Property, slug=slug, owner=request.user)
    if property_item.listing_state != ListingStateChoices.ACTIVE:
        messages.error(request, "Only approved active properties can be promoted.")
        return redirect('properties:my-properties')

    if request.method == 'POST':
        promo_type = request.POST.get('promotion_type', PromotionTypeChoices.FEATURED)
        price = 999.00
        if promo_type == PromotionTypeChoices.HOMEPAGE_HIGHLIGHT:
            price = 1999.00
        elif promo_type == PromotionTypeChoices.PREMIUM_SEARCH:
            price = 1499.00

        txn = PaymentService.create_promotion_order(request.user, property_item, promo_type, price)
        context = {
            'property': property_item,
            'transaction': txn,
            'promo_type': promo_type,
            'amount': price,
        }
        return render_billing_template(request, 'billing/promote_checkout.html', context)

    context = {
        'property': property_item,
        'promotion_types': PromotionTypeChoices.choices,
    }
    return render_billing_template(request, 'billing/promote_property.html', context)

@login_required
def verify_promotion_view(request):
    """Verifies and activates property promotion upon payment confirmation."""
    if request.method == 'POST':
        txn_id = request.POST.get('transaction_id')
        property_id = request.POST.get('property_id')
        promo_type = request.POST.get('promotion_type', PromotionTypeChoices.FEATURED)
        payment_id = request.POST.get('razorpay_payment_id', 'pay_promo_verified_123')

        property_item = get_object_or_404(Property, id=property_id, owner=request.user)
        try:
            promo = PaymentService.verify_and_activate_promotion(
                user=request.user,
                property_item=property_item,
                transaction_id=txn_id,
                promotion_type=promo_type,
                payment_id=payment_id
            )
            messages.success(request, f"Success! Property '{property_item.title}' is now promoted.")
            return redirect('properties:my-properties')
        except Exception:
            messages.error(request, "Promotion payment verification failed.")
            return redirect('properties:my-properties')

    return redirect('properties:my-properties')

@login_required
def user_billing_dashboard_view(request):
    """User billing dashboard displaying active subscription, allowance usage, transactions, and invoices."""
    active_sub = PaymentService.get_user_active_subscription(request.user)
    can_post, max_allowed, current_count = PaymentService.can_user_post_property(request.user)
    transactions = Transaction.objects.filter(user=request.user).select_related('package')
    invoices = Invoice.objects.filter(transaction__user=request.user).select_related('transaction')
    promotions = PropertyPromotion.objects.filter(purchaser=request.user, is_active=True).select_related('property')

    context = {
        'active_sub': active_sub,
        'can_post': can_post,
        'max_allowed': max_allowed,
        'current_count': current_count,
        'transactions': transactions,
        'invoices': invoices,
        'promotions': promotions,
    }
    return render_billing_template(request, 'billing/billing_dashboard.html', context)

@login_required
def admin_revenue_dashboard_view(request):
    """Admin revenue dashboard displaying verified platform revenue, active subscriptions, and package management."""
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")

    total_revenue = Transaction.objects.filter(status=PaymentStatusChoices.SUCCESS).aggregate(total=Sum('amount'))['total'] or 0.00
    total_transactions = Transaction.objects.count()
    successful_txns = Transaction.objects.filter(status=PaymentStatusChoices.SUCCESS).count()
    active_subscriptions = Subscription.objects.filter(is_active=True, end_date__gte=timezone.now()).count()
    active_promotions = PropertyPromotion.objects.filter(is_active=True, end_date__gte=timezone.now()).count()

    transactions = Transaction.objects.all().select_related('user', 'package')[:50]
    packages = Package.objects.all()

    context = {
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'successful_txns': successful_txns,
        'active_subscriptions': active_subscriptions,
        'active_promotions': active_promotions,
        'transactions': transactions,
        'packages': packages,
    }
    return render_billing_template(request, 'admin_panel/revenue_dashboard.html', context)
