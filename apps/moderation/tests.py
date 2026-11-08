from django.test import TestCase, Client
from django.template import Context
from django.urls import reverse
from apps.accounts.models import User, RoleChoices
from apps.locations.models import State, City, Locality
from apps.properties.models import Property, PropertyType, ListingPurposeChoices, PropertyCategoryChoices, ListingStateChoices
from apps.moderation.models import AuditLog

Context.__copy__ = lambda self: self

class AdminPanelAndModerationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='Password123'
        )
        self.owner = User.objects.create_user(
            username='testowner',
            email='owner@example.com',
            password='Password123',
            role=RoleChoices.OWNER
        )

        self.state, _ = State.objects.get_or_create(code='MH', defaults={'name': 'Maharashtra'})
        self.city = City.objects.create(state=self.state, name='Mumbai', slug='mumbai', is_active=True)
        self.locality = Locality.objects.create(city=self.city, name='Bandra', slug='bandra')
        self.apt_type = PropertyType.objects.create(name='Apartment', slug='apartment', category=PropertyCategoryChoices.RESIDENTIAL)

        self.prop_pending = Property.objects.create(
            title='Pending Review Property',
            slug='pending-review-property',
            description='Pending description',
            listing_purpose=ListingPurposeChoices.BUY,
            property_category=PropertyCategoryChoices.RESIDENTIAL,
            property_type=self.apt_type,
            owner=self.owner,
            posted_by_user=self.owner,
            price=15000000.00,
            carpet_area=1200.00,
            address='Bandra West',
            city=self.city,
            locality=self.locality,
            listing_state=ListingStateChoices.PENDING_APPROVAL
        )

    def test_admin_access_control(self):
        """Test that unauthenticated users and non-admin users (owners) are denied access to admin panel."""
        admin_url = reverse('moderation:dashboard')

        # Unauthenticated denied (redirects to login)
        response = self.client.get(admin_url)
        self.assertNotEqual(response.status_code, 200)

        # Owner denied (403 Forbidden)
        self.client.force_login(self.owner)
        response = self.client.get(admin_url)
        self.assertEqual(response.status_code, 403)

        # Superuser / Admin allowed
        self.client.force_login(self.admin_user)
        response = self.client.get(admin_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Platform Overview')

    def test_property_approval_moderation_workflow(self):
        """Test approving a pending property listing and generating an audit log."""
        self.client.force_login(self.admin_user)
        approve_url = reverse('moderation:approve-property', kwargs={'pk': self.prop_pending.id})

        response = self.client.post(approve_url, follow=True)
        self.assertEqual(response.status_code, 200)

        self.prop_pending.refresh_from_db()
        self.assertEqual(self.prop_pending.listing_state, ListingStateChoices.ACTIVE)
        self.assertEqual(AuditLog.objects.filter(action='APPROVE_PROPERTY', entity_id=str(self.prop_pending.id)).count(), 1)

    def test_property_rejection_moderation_workflow(self):
        """Test rejecting a pending property listing with a reason and generating an audit log."""
        self.client.force_login(self.admin_user)
        reject_url = reverse('moderation:reject-property', kwargs={'pk': self.prop_pending.id})

        response = self.client.post(reject_url, {'rejection_reason': 'Incomplete documentation.'}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.prop_pending.refresh_from_db()
        self.assertEqual(self.prop_pending.listing_state, ListingStateChoices.REJECTED)
        self.assertEqual(self.prop_pending.rejection_reason, 'Incomplete documentation.')
        self.assertEqual(AuditLog.objects.filter(action='REJECT_PROPERTY', entity_id=str(self.prop_pending.id)).count(), 1)

    def test_user_management_and_status_toggle(self):
        """Test viewing users and toggling user active status securely."""
        self.client.force_login(self.admin_user)
        toggle_url = reverse('moderation:toggle-user', kwargs={'pk': self.owner.id})

        response = self.client.post(toggle_url, follow=True)
        self.assertEqual(response.status_code, 200)

        self.owner.refresh_from_db()
        self.assertFalse(self.owner.is_active)
        self.assertEqual(AuditLog.objects.filter(action='TOGGLE_USER_STATUS', entity_id=str(self.owner.id)).count(), 1)
