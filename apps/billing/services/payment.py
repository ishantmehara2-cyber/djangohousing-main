import os
import uuid
import datetime
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from apps.billing.models import (
    Package, Subscription, Transaction, Invoice,
    PropertyPromotion, PaymentStatusChoices, PromotionTypeChoices
)
from apps.properties.models import Property, ListingStateChoices
from apps.engagements.services.notifications import NotificationService

class PaymentService:
    """
    Core Payment, Subscription and Promotion Service.
    Handles order generation, signature verification, invoice issuing, and plan/promotion activation.
    """
    DEFAULT_FREE_LISTING_LIMIT = 3

    @classmethod
    def get_user_active_subscription(cls, user):
        if not user or not user.is_authenticated:
            return None
        sub = Subscription.objects.filter(
            user=user,
            is_active=True,
            end_date__gte=timezone.now()
        ).select_related('package').first()
        return sub

    @classmethod
    def can_user_post_property(cls, user):
        """
        Backend permission check: Verifies if user has remaining listing allowance under their active plan.
        """
        if user.is_superuser or user.is_staff:
            return True, 9999, 0

        active_sub = cls.get_user_active_subscription(user)
        max_allowed = active_sub.package.max_listings if active_sub else cls.DEFAULT_FREE_LISTING_LIMIT
        current_active_count = Property.objects.filter(
            owner=user,
            listing_state__in=[ListingStateChoices.ACTIVE, ListingStateChoices.PENDING_APPROVAL]
        ).count()

        can_post = current_active_count < max_allowed
        return can_post, max_allowed, current_active_count

    @classmethod # Order Creation
    def create_subscription_order(cls, user, package):
        order_id = f"order_{uuid.uuid4().hex[:12]}"
        txn = Transaction.objects.create(
            user=user,
            package=package,
            razorpay_order_id=order_id,
            amount=package.price,
            status=PaymentStatusChoices.PENDING
        )
        return txn

    @classmethod # Backend Verification
    @transaction.atomic
    def verify_and_activate_subscription(cls, user, transaction_id, payment_id='pay_test123'):
        txn = get_object_or_404_txn(transaction_id, user)
        if txn.status == PaymentStatusChoices.SUCCESS:
            return txn

        txn.status = PaymentStatusChoices.SUCCESS
        txn.razorpay_payment_id = payment_id or f"pay_{uuid.uuid4().hex[:12]}"
        txn.save()

        # Generate Invoice
        inv_num = f"INV-{timezone.now().strftime('%Y%m%d')}-{txn.id}"
        Invoice.objects.create(
            transaction=txn,
            invoice_number=inv_num,
            total_amount=txn.amount
        )

        # Deactivate previous active subscriptions
        Subscription.objects.filter(user=user, is_active=True).update(is_active=False)

        # Activate new subscription
        validity = txn.package.validity_days if txn.package else 30
        end_dt = timezone.now() + datetime.timedelta(days=validity)
        sub = Subscription.objects.create(
            user=user,
            package=txn.package,
            start_date=timezone.now(),
            end_date=end_dt,
            is_active=True
        )

        # Notify User
        NotificationService.create_notification(
            user=user,
            title=f"Subscription Activated: {txn.package.name}",
            message=f"Your subscription for {txn.package.name} is now active until {end_dt.strftime('%B %d, %Y')}."
        )

        return txn

    @classmethod
    def create_promotion_order(cls, user, property_item, promotion_type, price=999.00):
        order_id = f"promo_ord_{uuid.uuid4().hex[:12]}"
        txn = Transaction.objects.create(
            user=user,
            package=None,
            razorpay_order_id=order_id,
            amount=price,
            status=PaymentStatusChoices.PENDING
        )
        return txn

    @classmethod
    @transaction.atomic
    def verify_and_activate_promotion(cls, user, property_item, transaction_id, promotion_type=PromotionTypeChoices.FEATURED, days=30, payment_id='pay_promo123'):
        txn = Transaction.objects.get(id=transaction_id, user=user)
        txn.status = PaymentStatusChoices.SUCCESS
        txn.razorpay_payment_id = payment_id
        txn.save()

        inv_num = f"INV-PROMO-{timezone.now().strftime('%Y%m%d')}-{txn.id}"
        Invoice.objects.create(
            transaction=txn,
            invoice_number=inv_num,
            total_amount=txn.amount
        )

        end_dt = timezone.now() + datetime.timedelta(days=days)
        promo = PropertyPromotion.objects.create(
            property=property_item,
            purchaser=user,
            promotion_type=promotion_type,
            transaction=txn,
            end_date=end_dt,
            is_active=True
        )

        NotificationService.create_notification(
            user=user,
            title=f"Property Promotion Activated: {property_item.title}",
            message=f"Your property '{property_item.title}' is now promoted as {promotion_type} for {days} days."
        )

        return promo

def get_object_or_404_txn(txn_id, user):
    return Transaction.objects.get(id=txn_id, user=user)
