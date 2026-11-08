from django.test import TestCase, Client
from django.urls import reverse
from apps.services.models import BankPartner, BankLoanEnquiry, RentalAgreementRequest, AgreementType
from apps.properties.models import Property, PropertyType
from apps.locations.models import State, City, Locality
from apps.accounts.models import User, RoleChoices
from apps.properties.services.lets_api_adapter import LetsApiAdapter

class FinancialAndRentalServicesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.bank = BankPartner.objects.create(
            name="Test National Bank",
            slug="test-national-bank",
            min_interest_rate=8.50,
            max_tenure_years=30
        )
        self.state, _ = State.objects.get_or_create(code="MH", defaults={'name': 'Maharashtra'})
        self.city = City.objects.create(name="Mumbai", slug="mumbai", state=self.state)
        self.locality = Locality.objects.create(name="Andheri", slug="andheri", city=self.city)
        self.property_type = PropertyType.objects.create(name="Apartment", slug="apartment")
        self.owner = User.objects.create_user(
            username="owner_user",
            email="owner@example.com",
            password="Password123!",
            role=RoleChoices.OWNER
        )
        self.property = Property.objects.create(
            title="Luxury 3BHK Apartment",
            slug="luxury-3bhk-apartment",
            description="Spacious home",
            property_type=self.property_type,
            owner=self.owner,
            posted_by_user=self.owner,
            price=12000000.00,
            carpet_area=1200.00,
            city=self.city,
            locality=self.locality,
            address="123 Main Road"
        )

    def test_bank_loans_view(self):
        response = self.client.get(reverse('services:bank-loans'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test National Bank")

    def test_bank_loan_enquiry_submission(self):
        post_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '9876543210',
            'employment_type': 'SALARIED',
            'monthly_income': '100000',
            'desired_loan_amount': '5000000',
            'preferred_bank': self.bank.id
        }
        response = self.client.post(reverse('services:bank-loans'), post_data)
        self.assertRedirects(response, reverse('services:bank-loans'))
        self.assertTrue(BankLoanEnquiry.objects.filter(email='john@example.com').exists())

    def test_home_loan_calculator_calculation(self):
        calc_params = {
            'monthly_income': '100000',
            'existing_emi': '10000',
            'tenure_years': '20',
            'interest_rate': '8.5',
            'foir_percentage': '50'
        }
        response = self.client.get(reverse('services:loan-calculator'), calc_params)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "₹")

    def test_rental_agreement_request_submission(self):
        post_data = {
            'full_name': 'Alice Smith',
            'email': 'alice@example.com',
            'phone': '9876500000',
            'agreement_type': AgreementType.E_STAMP,
            'property_address': 'Flat 401, Sunshine Heights',
            'city_name': 'Mumbai',
            'monthly_rent': '30000',
            'security_deposit': '100000',
            'tenancy_period_months': 11,
            'lock_in_period_months': 1,
            'notes': 'No pets clause'
        }
        response = self.client.post(reverse('services:rental-agreement'), post_data)
        req_obj = RentalAgreementRequest.objects.get(email='alice@example.com')
        self.assertRedirects(response, reverse('services:rental-agreement-detail', kwargs={'ref_num': req_obj.reference_number}))
        self.assertTrue(req_obj.reference_number.startswith('RA-'))

    def test_lets_api_adapter_payload_building(self):
        payload = LetsApiAdapter.build_payload(self.property)
        self.assertEqual(payload['external_id'], str(self.property.id))
        self.assertEqual(payload['title'], "Luxury 3BHK Apartment")
        self.assertEqual(payload['location']['city'], "Mumbai")
        self.assertEqual(payload['pricing']['amount'], 12000000.00)
