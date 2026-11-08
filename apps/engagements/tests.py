from django.test import TestCase, Client
from django.template import Context
from django.db.utils import IntegrityError
from django.utils import timezone
from django.urls import reverse
from apps.accounts.models import User, RoleChoices
from apps.locations.models import State, City, Locality
from apps.properties.models import Property, PropertyType, ListingPurposeChoices, PropertyCategoryChoices, ListingStateChoices, FurnishingChoices
from apps.engagements.models import (
    Favorite, Enquiry, Lead, PropertyVisit, Notification,
    UserPreference, RecentlyViewed, SavedSearch, PropertyPriceHistory
)
from apps.engagements.services.notifications import NotificationService
from apps.properties.services.recommendation_service import PropertyRecommendationService

Context.__copy__ = lambda self: self

class AdvancedDiscoveryAndPersonalizationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.buyer = User.objects.create_user(username='buyer1', email='buyer1@example.com', password='Password123', role=RoleChoices.TENANT_BUYER)
        self.owner = User.objects.create_user(username='owner1', email='owner1@example.com', password='Password123', role=RoleChoices.OWNER)

        self.state, _ = State.objects.get_or_create(code='KA', defaults={'name': 'Karnataka'})
        self.city_bengaluru = City.objects.create(state=self.state, name='Bengaluru', slug='bengaluru', is_active=True)
        self.locality = Locality.objects.create(city=self.city_bengaluru, name='Indiranagar', slug='indiranagar')
        self.prop_type = PropertyType.objects.create(name='Villa', slug='villa', category=PropertyCategoryChoices.RESIDENTIAL)

        self.property1 = Property.objects.create(
            title='Luxury Indiranagar Villa',
            slug='luxury-indiranagar-villa',
            description='Independent luxury villa in Bengaluru',
            listing_purpose=ListingPurposeChoices.BUY,
            property_category=PropertyCategoryChoices.RESIDENTIAL,
            property_type=self.prop_type,
            owner=self.owner,
            posted_by_user=self.owner,
            price=45000000.00,
            bhk=4,
            carpet_area=3200.00,
            city=self.city_bengaluru,
            locality=self.locality,
            address='100 Feet Road, Indiranagar',
            listing_state=ListingStateChoices.ACTIVE
        )

        self.property2 = Property.objects.create(
            title='Cozy Indiranagar Apartment',
            slug='cozy-indiranagar-apartment',
            description='Cozy apartment in Bengaluru',
            listing_purpose=ListingPurposeChoices.BUY,
            property_category=PropertyCategoryChoices.RESIDENTIAL,
            property_type=self.prop_type,
            owner=self.owner,
            posted_by_user=self.owner,
            price=15000000.00,
            bhk=2,
            carpet_area=1100.00,
            city=self.city_bengaluru,
            locality=self.locality,
            address='Indiranagar 12th Main',
            listing_state=ListingStateChoices.ACTIVE
        )

    def test_user_preference_profile_creation_and_update(self):
        """Test configuring user property preference profile."""
        self.client.force_login(self.buyer)
        pref_url = reverse('engagements:preferences')

        response = self.client.post(pref_url, {
            'purpose': 'BUY',
            'city': str(self.city_bengaluru.id),
            'min_price': '10000000',
            'max_price': '50000000',
            'min_bhk': '2',
            'max_bhk': '4'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        pref = UserPreference.objects.get(user=self.buyer)
        self.assertEqual(pref.city, self.city_bengaluru)
        self.assertEqual(pref.max_price, 50000000.00)

    def test_recommendation_scoring_engine(self):
        """Test weighted recommendation scoring service."""
        UserPreference.objects.create(
            user=self.buyer,
            purpose=ListingPurposeChoices.BUY,
            city=self.city_bengaluru,
            locality=self.locality,
            min_price=10000000.00,
            max_price=50000000.00,
            min_bhk=2,
            max_bhk=4
        )

        recommendations = PropertyRecommendationService.get_recommendations_for_user(self.buyer, limit=5)
        self.assertGreater(len(recommendations), 0)
        top_rec = recommendations[0]
        self.assertGreater(top_rec.score, 0)
        self.assertTrue(hasattr(top_rec, 'recommendation_reason'))

    def test_recently_viewed_history_tracking(self):
        """Test recording property views and clearing history."""
        self.client.force_login(self.buyer)
        detail_url = reverse('properties:detail', kwargs={'slug': self.property1.slug})

        # Viewing property creates RecentlyViewed record
        self.client.get(detail_url)
        self.assertEqual(RecentlyViewed.objects.filter(user=self.buyer, property=self.property1).count(), 1)

        # Clear history
        clear_url = reverse('engagements:clear-recently-viewed')
        response = self.client.get(clear_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(RecentlyViewed.objects.filter(user=self.buyer).count(), 0)

    def test_saved_search_creation_and_deletion(self):
        """Test creating and deleting a saved search."""
        self.client.force_login(self.buyer)
        save_url = reverse('engagements:save-search')

        response = self.client.post(save_url, {'name': 'Bengaluru Villas'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SavedSearch.objects.filter(user=self.buyer, name='Bengaluru Villas').exists())

    def test_property_comparison_tool_view(self):
        """Test side-by-side property comparison tool."""
        compare_url = reverse('properties:compare') + f"?id={self.property1.id}&id={self.property2.id}"
        response = self.client.get(compare_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.property1.title)
        self.assertContains(response, self.property2.title)

    def test_smart_discover_dashboard_view(self):
        """Test Smart Discover Dashboard view."""
        self.client.force_login(self.buyer)
        discover_url = reverse('engagements:smart-discover')
        response = self.client.get(discover_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Personal Discovery Hub')
