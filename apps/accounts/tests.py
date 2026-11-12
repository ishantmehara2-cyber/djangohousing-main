from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import RoleChoices, UserStatusChoices
from apps.accounts.forms import UserRegistrationForm
from apps.locations.models import State, City, Locality
from apps.properties.models import Property, PropertyType, ListingPurposeChoices, ListingStateChoices
from apps.engagements.models import Enquiry, Lead
from apps.services.models import EmailOTP, OTPPurposeChoices
import django.test.client

# Neutralize store_rendered_templates for Python 3.14 copy compatibility
django.test.client.store_rendered_templates = lambda *args, **kwargs: None

User = get_user_model()

class AuthenticationAndOTPWorkflowsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.state, _ = State.objects.get_or_create(code='MH', defaults={'name': 'Maharashtra'})
        self.city = City.objects.create(state=self.state, name='Mumbai', slug='mumbai')
        self.locality = Locality.objects.create(name='Andheri West', slug='andheri-west', city=self.city)
        self.prop_type = PropertyType.objects.create(name='Apartment', slug='apartment')

        # Create test users
        self.buyer_user = User.objects.create_user(
            username='buyer@example.com',
            email='buyer@example.com',
            phone='9876543210',
            password='TestPassword123!',
            first_name='John',
            last_name='Buyer',
            role=RoleChoices.BUYER
        )

        self.owner_user = User.objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            phone='9876543211',
            password='TestPassword123!',
            first_name='Jane',
            last_name='Owner',
            role=RoleChoices.OWNER
        )

        self.property_item = Property.objects.create(
            title='Luxury Sea Facing Apartment',
            slug='luxury-sea-facing-apartment',
            description='Gorgeous 3BHK flat in Andheri West',
            listing_purpose=ListingPurposeChoices.BUY,
            property_type=self.prop_type,
            owner=self.owner_user,
            posted_by_user=self.owner_user,
            price=15000000.0,
            bhk=3,
            carpet_area=1200.0,
            city=self.city,
            locality=self.locality,
            address='123 Marine Drive',
            listing_state=ListingStateChoices.ACTIVE
        )

    def test_registration_otp_workflow(self):
        # 1. Registration POST
        from django.core.files.uploadedfile import SimpleUploadedFile
        doc_file = SimpleUploadedFile("gumasta.pdf", b"%PDF-1.4 test doc", content_type="application/pdf")
        reg_response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Alice',
            'last_name': 'Partner',
            'email': 'alice@example.com',
            'phone': '9123456789',
            'role': RoleChoices.PARTNER,
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'agency_name': 'Alice Realty',
            'business_address': '101 Trade Center',
            'business_state': 'Maharashtra',
            'business_city': 'Mumbai',
            'business_pincode': '400050',
            'declaration_accepted': 'on',
            'doc_category_1': 'GUMASTA',
            'doc_file_1': doc_file
        })
        self.assertRedirects(reg_response, reverse('accounts:verify_otp'))

        # Check Email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Verify your email address | Housing", mail.outbox[0].subject)
        self.assertIn("Housing <", mail.outbox[0].from_email)

        # Retrieve OTP record
        otp_obj, code = EmailOTP.generate_otp('alice@example.com', purpose=OTPPurposeChoices.REGISTER, bypass_cooldown=True)

        # 2. Invalid OTP verification
        invalid_res = self.client.post(reverse('accounts:verify_otp'), {'otp': '000000'})
        self.assertEqual(invalid_res.status_code, 200)
        self.assertFalse(User.objects.filter(email='alice@example.com').exists())

        # 3. Valid OTP verification
        valid_res = self.client.post(reverse('accounts:verify_otp'), {'otp': code})
        self.assertTrue(User.objects.filter(email='alice@example.com').exists())
        alice = User.objects.get(email='alice@example.com')
        self.assertTrue(alice.is_active)
        self.assertTrue(alice.email_verified)

    def test_two_factor_login_otp_workflow(self):
        # Step 1: Login POST with correct credentials
        login_res = self.client.post(reverse('accounts:login'), {
            'email': 'buyer@example.com',
            'password': 'TestPassword123!'
        })
        self.assertRedirects(login_res, reverse('accounts:verify_login_otp'))
        self.assertFalse('_auth_user_id' in self.client.session)

        # Email sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Your login verification code | Housing", mail.outbox[0].subject)

        # Step 2: Verify Login OTP
        otp_obj, code = EmailOTP.generate_otp('buyer@example.com', purpose=OTPPurposeChoices.LOGIN, user=self.buyer_user, bypass_cooldown=True)
        verify_res = self.client.post(reverse('accounts:verify_login_otp'), {'otp': code})
        self.assertRedirects(verify_res, reverse('accounts:buyer_dashboard'))

        # Verify authenticated session established
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.buyer_user.id)

    def test_direct_property_interest_and_owner_notification(self):
        self.client.force_login(self.buyer_user)

        # 1. Directly express interest in property (NO OTP required)
        interest_res = self.client.post(reverse('engagements:send-inquiry', args=[self.property_item.slug]), {
            'message': 'I am highly interested in buying this flat.'
        })
        self.assertRedirects(interest_res, reverse('properties:detail', args=[self.property_item.slug]))

        # Verify Enquiry & Lead created in DB
        self.assertTrue(Enquiry.objects.filter(property=self.property_item, sender_user=self.buyer_user).exists())
        self.assertTrue(Lead.objects.filter(property=self.property_item, lead_user=self.buyer_user).exists())

        # Verify Owner notification email directly dispatched with buyer's email & phone
        self.assertGreaterEqual(len(mail.outbox), 1)
        owner_email = mail.outbox[-1]
        self.assertIn("New property enquiry received | Housing", owner_email.subject)
        self.assertEqual(owner_email.to, [self.owner_user.email])
        self.assertIn(self.buyer_user.email, owner_email.body)
        self.assertIn(self.buyer_user.phone, owner_email.body)

    def test_expired_and_purpose_mismatch_otp_rejection(self):
        otp_obj, code = EmailOTP.generate_otp('buyer@example.com', purpose=OTPPurposeChoices.LOGIN, bypass_cooldown=True)

        # Test purpose mismatch
        is_valid, msg = otp_obj.verify(code, expected_purpose=OTPPurposeChoices.REGISTER)
        self.assertFalse(is_valid)
        self.assertIn("mismatch", msg.lower())

        # Test expired OTP
        otp_obj.expires_at = timezone.now() - timedelta(minutes=1)
        otp_obj.save()
        is_valid_expired, msg_expired = otp_obj.verify(code, expected_purpose=OTPPurposeChoices.LOGIN)
        self.assertFalse(is_valid_expired)
        self.assertIn("expired", msg_expired.lower())

    def test_property_mismatch_otp_rejection(self):
        other_prop = Property.objects.create(
            title='Another Flat',
            slug='another-flat',
            description='Test flat',
            listing_purpose=ListingPurposeChoices.RENT,
            property_type=self.prop_type,
            owner=self.owner_user,
            posted_by_user=self.owner_user,
            rent=25000.0,
            carpet_area=800.0,
            city=self.city,
            locality=self.locality,
            address='456 Link Road',
            listing_state=ListingStateChoices.ACTIVE
        )

        otp_obj, code = EmailOTP.generate_otp(
            email=self.buyer_user.email,
            purpose=OTPPurposeChoices.PROPERTY_INTEREST,
            property_obj=self.property_item,
            bypass_cooldown=True
        )

        # Attempt to verify using wrong property ID
        is_valid, msg = otp_obj.verify(code, expected_purpose=OTPPurposeChoices.PROPERTY_INTEREST, expected_property_id=other_prop.id)
        self.assertFalse(is_valid)
        self.assertIn("not valid for this property", msg.lower())
