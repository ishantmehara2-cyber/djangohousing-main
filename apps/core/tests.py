from django.test import TestCase, RequestFactory, Client
from apps.accounts.models import User
from apps.locations.models import State, City, Locality
from apps.properties.models import PropertyType, Property, PropertyCategoryChoices, ListingPurposeChoices
from apps.core.models import FAQCategory, FAQItem, SupportTicket, TicketCategoryChoices

class Phase15CoreAndSupportTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.state, _ = State.objects.get_or_create(code='MH', defaults={'name': 'Maharashtra'})
        self.city = City.objects.create(state=self.state, name='Mumbai', slug='mumbai', is_popular=True, is_active=True)
        self.locality = Locality.objects.create(city=self.city, name='Andheri', slug='andheri', pincode='400053')
        self.property_type = PropertyType.objects.create(name='Apartment', slug='apartment', category=PropertyCategoryChoices.RESIDENTIAL)

        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='Password123!',
            first_name='Amit',
            role='BUYER'
        )

        self.owner = User.objects.create_user(
            username='testowner',
            email='owner@test.com',
            password='Password123!',
            first_name='Vikram',
            role='OWNER'
        )

        self.property = Property.objects.create(
            title='Luxury 3BHK Apartment in Andheri',
            slug='luxury-3bhk-andheri',
            description='Spacious luxury apartment with modern amenities.',
            listing_purpose=ListingPurposeChoices.BUY,
            property_category=PropertyCategoryChoices.RESIDENTIAL,
            property_type=self.property_type,
            owner=self.owner,
            posted_by_user=self.owner,
            price=15000000,
            carpet_area=1400,
            address='Linking Road',
            city=self.city,
            locality=self.locality,
            listing_state='ACTIVE'
        )

        self.faq_cat = FAQCategory.objects.create(name='General', slug='general', display_order=1)
        self.faq_item = FAQItem.objects.create(category=self.faq_cat, question='How to buy?', answer='Search and contact owners.')

    def test_legal_pages_return_200(self):
        """Test that all legal and business pages load successfully."""
        urls = ['/about/', '/contact/', '/terms/', '/privacy/', '/cookie-policy/', '/listing-guidelines/', '/refund-policy/', '/payment-terms/', '/disclaimer/', '/grievance/']
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Failed on URL: {url}")

    def test_help_centre_and_faq(self):
        """Test help centre search and FAQ rendering."""
        response = self.client.get('/help/', {'q': 'buy'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'How to buy?', response.content)

    def test_support_ticket_workflow(self):
        """Test support ticket creation and list view for authenticated user."""
        self.client.login(username='testuser', password='Password123!')

        # Create ticket
        response = self.client.post('/support/new/', {
            'category': TicketCategoryChoices.ACCOUNT,
            'subject': 'Login Issue',
            'description': 'Cannot reset password.',
            'priority': 'HIGH'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login Issue', response.content)

        # Check ticket list
        response = self.client.get('/support/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login Issue', response.content)

    def test_robots_and_sitemap(self):
        """Test robots.txt and sitemap.xml endpoints."""
        res_robots = self.client.get('/robots.txt')
        self.assertEqual(res_robots.status_code, 200)
        self.assertIn(b'Sitemap:', res_robots.content)

        res_sitemap = self.client.get('/sitemap.xml')
        self.assertEqual(res_sitemap.status_code, 200)
        self.assertIn(b'luxury-3bhk-andheri', res_sitemap.content)

    def test_health_check_endpoint(self):
        """Test health check JSON endpoint."""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')

    def test_property_report_view(self):
        """Test authenticated user reporting a property."""
        self.client.login(username='testuser', password='Password123!')
        response = self.client.post(f'/admin-panel/property/{self.property.slug}/report/', {
            'reason_category': 'MISLEADING_PRICE',
            'reason': 'Price listed is incorrect.'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.property.reports.exists())
