from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from apps.services.models import BankPartner, BankLoanEnquiry, RentalAgreementRequest, AgreementType, BankCategoryChoices
from apps.properties.models import Property, PropertyType
from apps.locations.models import State, City, Locality
from apps.accounts.models import User, RoleChoices
import django.test.client

django.test.client.store_rendered_templates = lambda *args, **kwargs: None

class BankManagementAndServicesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin_user",
            email="admin@example.com",
            password="AdminPassword123!",
            role=RoleChoices.ADMIN
        )
        self.customer_user = User.objects.create_user(
            username="customer_user",
            email="customer@example.com",
            password="CustomerPassword123!",
            role=RoleChoices.BUYER
        )

        self.hdfc = BankPartner.objects.get(slug="hdfc-bank")
        self.sbi = BankPartner.objects.get(slug="state-bank-of-india-sbi")
        self.icici = BankPartner.objects.get(slug="icici-bank")

    def test_1_admin_adds_new_bank_kotak(self):
        """TEST 1: Admin adds Kotak Mahindra Bank -> appears automatically on public Bank Loans page."""
        self.client.force_login(self.admin_user)
        add_data = {
            'name': 'Kotak Mahindra Bank',
            'slug': 'kotak-mahindra-bank',
            'category': BankCategoryChoices.PRIVATE_SECTOR,
            'display_order': 5,
            'is_active': True,
            'min_interest_rate': '8.70',
            'max_tenure_years': '30',
            'processing_fee_info': '0.50% or ₹10,000 + GST',
            'benefits_raw': 'Instant digital sanction\nSpecial interest concessions'
        }
        response = self.client.post(reverse('services:admin-add-bank'), add_data)
        self.assertRedirects(response, reverse('services:admin-bank-management'))

        kotak = BankPartner.objects.get(slug='kotak-mahindra-bank')
        self.assertEqual(float(kotak.min_interest_rate), 8.70)
        self.assertIn("Instant digital sanction", kotak.get_benefits_list)

        public_res = self.client.get(reverse('services:bank-loans'))
        self.assertEqual(public_res.status_code, 200)
        self.assertContains(public_res, "Kotak Mahindra Bank")
        self.assertContains(public_res, "From 8.70%")

    def test_2_admin_edits_hdfc_interest_rate(self):
        """TEST 2: Admin edits HDFC Bank interest rate -> updated rate appears on public page."""
        self.client.force_login(self.admin_user)
        edit_data = {
            'name': 'HDFC Bank',
            'slug': 'hdfc-bank',
            'category': BankCategoryChoices.PRIVATE_SECTOR,
            'display_order': 1,
            'is_active': True,
            'min_interest_rate': '8.75',
            'max_tenure_years': '30',
            'processing_fee_info': '0.50% of loan amount + GST',
            'benefits_raw': 'Instant digital sanction'
        }
        response = self.client.post(reverse('services:admin-edit-bank', kwargs={'pk': self.hdfc.id}), edit_data)
        self.assertRedirects(response, reverse('services:admin-bank-management'))

        self.hdfc.refresh_from_db()
        self.assertEqual(float(self.hdfc.min_interest_rate), 8.75)

        public_res = self.client.get(reverse('services:bank-loans'))
        self.assertContains(public_res, "From 8.75%")

    def test_3_admin_changes_sbi_processing_fee(self):
        """TEST 3: Admin changes SBI processing fee -> new processing fee appears publicly."""
        self.client.force_login(self.admin_user)
        edit_data = {
            'name': 'State Bank of India (SBI)',
            'slug': 'state-bank-of-india-sbi',
            'category': BankCategoryChoices.PUBLIC_SECTOR,
            'display_order': 2,
            'is_active': True,
            'min_interest_rate': '8.40',
            'max_tenure_years': '30',
            'processing_fee_info': 'Zero Processing Fee Offer',
            'benefits_raw': 'Concession on CIBIL score 750+'
        }
        response = self.client.post(reverse('services:admin-edit-bank', kwargs={'pk': self.sbi.id}), edit_data)
        self.assertRedirects(response, reverse('services:admin-bank-management'))

        self.sbi.refresh_from_db()
        self.assertEqual(self.sbi.processing_fee_info, "Zero Processing Fee Offer")

        public_res = self.client.get(reverse('services:bank-loans'))
        self.assertContains(public_res, "Zero Processing Fee Offer")

    def test_4_admin_deactivates_icici_bank(self):
        """TEST 4: Admin deactivates ICICI Bank -> disappears from public page but stays manageable in admin portal."""
        self.client.force_login(self.admin_user)
        toggle_res = self.client.post(reverse('services:admin-toggle-bank-active', kwargs={'pk': self.icici.id}))
        self.assertRedirects(toggle_res, reverse('services:admin-bank-management'))

        self.icici.refresh_from_db()
        self.assertFalse(self.icici.is_active)

        public_res = self.client.get(reverse('services:bank-loans'))
        self.assertNotContains(public_res, "Apply via ICICI Bank")

        admin_res = self.client.get(reverse('services:admin-bank-management'))
        self.assertContains(admin_res, "ICICI Bank")

    def test_5_unauthorized_customer_admin_api_rejection(self):
        """TEST 5: Unauthorized customer attempts to access admin bank-management APIs -> 403 / Redirected."""
        self.client.force_login(self.customer_user)
        api_res = self.client.get(reverse('services:api-admin-banks-list'))
        self.assertIn(api_res.status_code, [302, 403])

        admin_view_res = self.client.get(reverse('services:admin-bank-management'))
        self.assertEqual(admin_view_res.status_code, 302)

    def test_6_admin_changes_display_order(self):
        """TEST 6: Admin changes display order -> public bank cards appear in new order."""
        self.sbi.display_order = 1
        self.sbi.save()
        self.hdfc.display_order = 10
        self.hdfc.save()

        public_res = self.client.get(reverse('services:bank-loans'))
        content = public_res.content.decode('utf-8')
        sbi_index = content.find("State Bank of India (SBI)")
        hdfc_index = content.find("HDFC Bank")

        self.assertTrue(sbi_index < hdfc_index)
