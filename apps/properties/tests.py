from django.test import TestCase, Client
from django.template import Context
from django.urls import reverse
import datetime
from apps.accounts.models import User, RoleChoices
from apps.locations.models import State, City, Locality
from apps.properties.models import (
    Property, PropertyType, Amenity, PropertyAmenity, PropertyMedia,
    ListingPurposeChoices, PropertyCategoryChoices, ListingStateChoices,
    FurnishingChoices, PossessionStatusChoices
)
from apps.engagements.models import Favorite, Enquiry, PropertyVisit

Context.__copy__ = lambda self: self

class HousingCloneComprehensiveTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='testowner',
            email='owner@example.com',
            password='Password123',
            role=RoleChoices.OWNER,
            partner_approval_status='APPROVED'
        )
        self.agent = User.objects.create_user(
            username='testagent',
            email='agent@example.com',
            password='Password123',
            role=RoleChoices.AGENT
        )
        self.buyer = User.objects.create_user(
            username='testbuyer',
            email='buyer@example.com',
            password='Password123',
            role=RoleChoices.BUYER
        )
        self.tenant = User.objects.create_user(
            username='testtenant',
            email='tenant@example.com',
            password='Password123',
            role=RoleChoices.TENANT
        )

        self.state, _ = State.objects.get_or_create(code='MH', defaults={'name': 'Maharashtra'})
        self.city_mumbai = City.objects.create(state=self.state, name='Mumbai', slug='mumbai', is_active=True, is_popular=True)
        self.city_pune = City.objects.create(state=self.state, name='Pune', slug='pune', is_active=True, is_popular=True)

        self.locality_powai = Locality.objects.create(city=self.city_mumbai, name='Powai', slug='powai', pincode='400076')
        self.locality_bandra = Locality.objects.create(city=self.city_mumbai, name='Bandra', slug='bandra', pincode='400050')

        self.apt_type = PropertyType.objects.create(name='Apartment', slug='apartment', category=PropertyCategoryChoices.RESIDENTIAL)
        self.comm_type = PropertyType.objects.create(name='Office Space', slug='office-space', category=PropertyCategoryChoices.COMMERCIAL)

        self.amenity_gym = Amenity.objects.create(name='Gymnasium', slug='gymnasium')
        self.amenity_pool = Amenity.objects.create(name='Swimming Pool', slug='swimming-pool')

        # 1. Active Buy Property
        self.prop_buy = Property.objects.create(
            title='Luxury 3 BHK Apartment in Bandra',
            slug='luxury-3bhk-bandra',
            description='Spacious 3 BHK with sea view and top-tier amenities',
            listing_purpose=ListingPurposeChoices.BUY,
            property_category=PropertyCategoryChoices.RESIDENTIAL,
            property_type=self.apt_type,
            owner=self.owner,
            posted_by_user=self.owner,
            price=25000000.00,
            bhk=3,
            carpet_area=1500.00,
            furnishing=FurnishingChoices.FULLY_FURNISHED,
            possession_status=PossessionStatusChoices.READY_TO_MOVE,
            address='Bandstand',
            city=self.city_mumbai,
            locality=self.locality_bandra,
            pincode='400050',
            latitude=19.0596,
            longitude=72.8295,
            listing_state=ListingStateChoices.ACTIVE,
            verification_state='VERIFIED'
        )
        PropertyAmenity.objects.create(property=self.prop_buy, amenity=self.amenity_gym)
        PropertyAmenity.objects.create(property=self.prop_buy, amenity=self.amenity_pool)

        # 2. Active Rent Property
        self.prop_rent = Property.objects.create(
            title='Furnished 2 BHK Rental in Powai',
            slug='furnished-2bhk-rent-powai',
            description='Ready to move 2 BHK near Powai lake',
            listing_purpose=ListingPurposeChoices.RENT,
            property_category=PropertyCategoryChoices.RESIDENTIAL,
            property_type=self.apt_type,
            owner=self.owner,
            posted_by_user=self.owner,
            rent=50000.00,
            bhk=2,
            carpet_area=1000.00,
            furnishing=FurnishingChoices.SEMI_FURNISHED,
            possession_status=PossessionStatusChoices.UNDER_CONSTRUCTION,
            address='Hiranandani',
            city=self.city_mumbai,
            locality=self.locality_powai,
            pincode='400076',
            listing_state=ListingStateChoices.ACTIVE
        )

        # 3. Draft Property (hidden publicly)
        self.prop_draft = Property.objects.create(
            title='Draft Property',
            slug='draft-property',
            description='Draft description',
            listing_purpose=ListingPurposeChoices.BUY,
            property_category=PropertyCategoryChoices.RESIDENTIAL,
            property_type=self.apt_type,
            owner=self.owner,
            posted_by_user=self.owner,
            price=10000000.00,
            bhk=1,
            carpet_area=500.00,
            address='Draft Address',
            city=self.city_mumbai,
            locality=self.locality_powai,
            listing_state=ListingStateChoices.DRAFT
        )

    def test_public_listing_and_catalog(self):
        """Phase 6 & 7: Test catalog listing views, buy/rent filtering, and search engine."""
        response = self.client.get(reverse('properties:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.prop_buy.title)
        self.assertNotContains(response, self.prop_draft.title)

        # Search by city and BHK
        response = self.client.get(reverse('properties:search'), {'city': 'mumbai', 'bhk': '3'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.prop_buy.title)
        self.assertNotContains(response, self.prop_rent.title)

    def test_property_details_and_engagements(self):
        """Phase 8: Test property details, enquiries, visit scheduling, and favorites."""
        detail_url = reverse('properties:detail', kwargs={'slug': self.prop_buy.slug})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.prop_buy.title)

        # Enquiry submission with OTP verification
        self.client.force_login(self.buyer)
        inquiry_url = reverse('engagements:send-inquiry', kwargs={'slug': self.prop_buy.slug})
        response = self.client.post(inquiry_url, {'message': 'Interested in buying.'}, follow=True)
        self.assertEqual(response.status_code, 200)

        from apps.services.models import EmailOTP, OTPPurposeChoices
        otp_obj, code = EmailOTP.generate_otp(self.buyer.email, purpose=OTPPurposeChoices.PROPERTY_INTEREST, user=self.buyer, property_obj=self.prop_buy, bypass_cooldown=True)
        verify_url = reverse('engagements:verify-property-interest-otp', kwargs={'pk': self.prop_buy.id})
        verify_res = self.client.post(verify_url, {'otp': code}, follow=True)
        self.assertEqual(verify_res.status_code, 200)
        self.assertEqual(Enquiry.objects.filter(property=self.prop_buy, sender_user=self.buyer).count(), 1)

        # Visit scheduling
        visit_url = reverse('engagements:schedule-visit', kwargs={'slug': self.prop_buy.slug})
        future_date = (datetime.date.today() + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        response = self.client.post(visit_url, {'visit_date': future_date, 'visit_time': '10:00'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PropertyVisit.objects.filter(property=self.prop_buy, visitor_user=self.buyer).count(), 1)

    def test_submission_permissions_and_workflow(self):
        """Phase 9: Test role-based submission, draft saving, admin approval submission, and editing moderation."""
        post_url = reverse('properties:post-property')

        # Buyer access denied
        self.client.force_login(self.buyer)
        response = self.client.get(post_url)
        self.assertEqual(response.status_code, 302)

        # Owner save as draft
        self.client.force_login(self.owner)
        response = self.client.post(post_url, {
            'title': 'New Test Draft',
            'description': 'Draft',
            'listing_purpose': 'BUY',
            'property_type': str(self.apt_type.id),
            'price': '7000000',
            'bhk': '2',
            'carpet_area': '800',
            'city': str(self.city_mumbai.id),
            'locality': str(self.locality_powai.id),
            'address': 'Test',
            'action': 'draft'
        })
        self.assertTrue(Property.objects.filter(title='New Test Draft', listing_state=ListingStateChoices.DRAFT).exists())

        # Owner edit active property triggers re-review
        edit_url = reverse('properties:edit', kwargs={'slug': self.prop_buy.slug})
        response = self.client.post(edit_url, {
            'title': 'Updated Luxury 3 BHK',
            'price': '26000000',
            'state': str(self.state.id),
            'city': str(self.city_mumbai.id),
            'locality': str(self.locality_bandra.id)
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.prop_buy.refresh_from_db()
        self.assertEqual(self.prop_buy.listing_state, ListingStateChoices.PENDING_APPROVAL)

    def test_dynamic_form_fields_admin_and_public_api(self):
        """Test creating, editing, and fetching dynamic property form fields and options."""
        admin_user = User.objects.create_superuser(username='admin', email='admin@example.com', password='Password123')
        self.client.force_login(admin_user)

        # 1. Create new field via admin API (Parking Availability)
        create_url = reverse('properties:api-admin-property-fields')
        response = self.client.post(create_url, {
            'key': 'parking_availability',
            'label': 'Parking Availability',
            'type': 'select',
            'required': True,
            'order': 5,
            'applicable_categories': ['RESIDENTIAL'],
            'applicable_listing_types': ['BUY', 'RENT']
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        field_id = data['id']

        # 2. Add options to the field
        options_url = reverse('properties:api-admin-property-field-options', kwargs={'pk': field_id})
        response = self.client.post(options_url, {
            'options': [
                {'label': 'Available', 'value': 'yes', 'order': 0},
                {'label': 'Not Available', 'value': 'no', 'order': 1}
            ]
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # 3. Fetch public configuration API
        public_url = reverse('properties:api-property-fields')
        response = self.client.get(public_url, {'category': 'RESIDENTIAL', 'listing_type': 'BUY'})
        self.assertEqual(response.status_code, 200)
        pub_data = response.json()
        self.assertTrue(pub_data['success'])
        fields_list = pub_data['data']['fields']
        field_keys = [f['key'] for f in fields_list]
        self.assertIn('parking_availability', field_keys)

        # 4. Test disable status
        status_url = reverse('properties:api-admin-property-field-status', kwargs={'pk': field_id})
        response = self.client.patch(status_url, {'is_active': False}, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # 5. Verify disabled field is not returned in public config
        response = self.client.get(public_url, {'category': 'RESIDENTIAL', 'listing_type': 'BUY'})
        pub_data = response.json()
        field_keys = [f['key'] for f in pub_data['data']['fields']]
        self.assertNotIn('parking_availability', field_keys)
