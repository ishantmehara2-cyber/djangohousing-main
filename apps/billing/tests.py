from django.test import TestCase, Client
from django.template import Context
from django.urls import reverse
from django.utils import timezone
import datetime

from apps.accounts.models import User, RoleChoices
from apps.locations.models import State, City, Locality
from apps.properties.models import Property, PropertyType, ListingPurposeChoices, PropertyCategoryChoices, ListingStateChoices
from apps.billing.models import (
    Package, Subscription, Transaction, Invoice,
    PropertyPromotion, PaymentStatusChoices, PromotionTypeChoices
)
from apps.billing.services.payment import PaymentService

Context.__copy__ = lambda self: self

class MonetizationAndBillingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='testowner',
            email='owner@example.com',
            password='Password123',
            role=RoleChoices.OWNER
        )
        self.admin = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='Password123'
        )

        self.state, _ = State.objects.get_or_create(code='MH', defaults={'name': 'Maharashtra'})
        self.city = City.objects.create(state=self.state, name='Mumbai', slug='mumbai', is_active=True)
        self.locality = Locality.objects.create(city=self.city, name='Andheri', slug='andheri')
        self.apt_type = PropertyType.objects.create(name='Apartment', slug='apartment', category=PropertyCategoryChoices.RESIDENTIAL)

        self.pkg_free = Package.objects.create(
            name='FREE',
            price=0.00,
            validity_days=30,
            max_listings=3,
            is_active=True
        )

        self.pkg_pro = Package.objects.create(
            name='PRO',
            price=2999.00,
            validity_days=30,
            max_listings=15,
            is_active=True
        )

        self.prop = Property.objects.create(
            title='Monetized Test Property',
            slug='monetized-test-property',
            description='Test property for promotion',
            listing_purpose=ListingPurposeChoices.BUY,
            property_category=PropertyCategoryChoices.RESIDENTIAL,
            property_type=self.apt_type,
            owner=self.owner,
            posted_by_user=self.owner,
            price=12000000.00,
            carpet_area=1100.00,
            address='Andheri West',
            city=self.city,
            locality=self.locality,
            listing_state=ListingStateChoices.ACTIVE
        )

    def test_pricing_page_view(self):
        """Test public pricing page loads successfully displaying available packages."""
        response = self.client.get(reverse('billing:pricing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FREE')
        self.assertContains(response, 'PRO')

    def test_order_creation_and_payment_verification(self):
        """Test subscription order creation, signature verification, and plan activation."""
        txn = PaymentService.create_subscription_order(self.owner, self.pkg_pro)
        self.assertEqual(txn.status, PaymentStatusChoices.PENDING)

        verified_txn = PaymentService.verify_and_activate_subscription(self.owner, txn.id, 'pay_test_verified_999')
        self.assertEqual(verified_txn.status, PaymentStatusChoices.SUCCESS)
        self.assertTrue(Invoice.objects.filter(transaction=verified_txn).exists())

        active_sub = PaymentService.get_user_active_subscription(self.owner)
        self.assertIsNotNone(active_sub)
        self.assertEqual(active_sub.package, self.pkg_pro)

    def test_listing_allowance_enforcement(self):
        """Test backend property listing allowance enforcement."""
        can_post, max_allowed, current_count = PaymentService.can_user_post_property(self.owner)
        self.assertTrue(can_post)
        self.assertEqual(max_allowed, PaymentService.DEFAULT_FREE_LISTING_LIMIT)

    def test_property_promotion_activation(self):
        """Test creating and activating a featured property promotion."""
        promo_txn = PaymentService.create_promotion_order(self.owner, self.prop, PromotionTypeChoices.FEATURED, 999.00)
        self.assertEqual(promo_txn.status, PaymentStatusChoices.PENDING)

        promo = PaymentService.verify_and_activate_promotion(
            user=self.owner,
            property_item=self.prop,
            transaction_id=promo_txn.id,
            promotion_type=PromotionTypeChoices.FEATURED,
            payment_id='pay_promo_test_999'
        )
        self.assertTrue(promo.is_active)
        self.assertEqual(promo.property, self.prop)

    def test_billing_dashboard_view(self):
        """Test user billing dashboard view."""
        self.client.force_login(self.owner)
        response = self.client.get(reverse('billing:billing-dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_revenue_dashboard(self):
        """Test admin revenue and financial analytics dashboard."""
        self.client.force_login(self.admin)
        response = self.client.get(reverse('billing:admin-revenue'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Total Verified Revenue')
