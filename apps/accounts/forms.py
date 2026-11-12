from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import PasswordResetForm
from apps.accounts.models import RoleChoices, PartnerDocumentTypeChoices
from apps.core.validators import validate_document_file, validate_file_size_5mb

User = get_user_model()

# Roles allowed for public user registration
ALLOWED_REGISTRATION_ROLES = [
    (RoleChoices.PARTNER, 'Real Estate Partner'),
]

class UserRegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'Enter full first name'
        })
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'Enter last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'name@example.com'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'e.g. 9876543210'
        })
    )
    role = forms.ChoiceField(
        choices=ALLOWED_REGISTRATION_ROLES,
        initial=RoleChoices.PARTNER,
        required=True,
        widget=forms.Select(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'id': 'id_role'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'Minimum 8 characters'
        })
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'Re-enter password'
        })
    )

    # Real Estate Partner Fields
    agency_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'Business or Agency Name (where applicable)'
        })
    )
    business_address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'rows': 2,
            'placeholder': 'Complete Business Address'
        })
    )
    business_state = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'State'
        })
    )
    business_city = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'City'
        })
    )
    business_locality = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'Locality / Area'
        })
    )
    business_pincode = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'PIN Code'
        })
    )

    # Property Listing Responsibility Declaration Checkbox
    declaration_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-brand-primary border-gray-300 rounded focus:ring-brand-primary',
            'id': 'id_declaration_accepted'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits_only = ''.join(c for c in phone if c.isdigit())
        if len(digits_only) < 10 or len(digits_only) > 15:
            raise ValidationError("Please enter a valid 10-15 digit phone number.")
        if User.objects.filter(phone=phone).exists():
            raise ValidationError("An account with this phone number already exists.")
        return phone

    def clean_role(self):
        role = self.cleaned_data.get('role', RoleChoices.PARTNER)
        if role not in [RoleChoices.PARTNER, RoleChoices.AGENT, RoleChoices.OWNER, RoleChoices.DEVELOPER]:
            role = RoleChoices.PARTNER
        return role

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
            else:
                temp_user = User(
                    username=cleaned_data.get('email', 'user'),
                    email=cleaned_data.get('email', ''),
                    first_name=cleaned_data.get('first_name', ''),
                    last_name=cleaned_data.get('last_name', '')
                )
                try:
                    validate_password(password, user=temp_user)
                except ValidationError as err:
                    self.add_error('password', err)

        declaration_accepted = cleaned_data.get('declaration_accepted')
        if not declaration_accepted:
            self.add_error('declaration_accepted', "You must accept the Property Listing Responsibility Declaration to register as a Real Estate Partner.")

        return cleaned_data

    def save(self):
        cd = self.cleaned_data
        role = cd.get('role') or RoleChoices.PARTNER

        user = User.objects.create_user(
            username=cd['email'],
            email=cd['email'],
            first_name=cd['first_name'],
            last_name=cd['last_name'],
            phone=cd['phone'],
            password=cd['password'],
            role=role,
            agency_name=cd.get('agency_name', ''),
            business_address=cd.get('business_address', ''),
            business_state=cd.get('business_state', ''),
            business_city=cd.get('business_city', ''),
            business_locality=cd.get('business_locality', ''),
            business_pincode=cd.get('business_pincode', ''),
            partner_approval_status='PENDING',
            declaration_accepted=cd.get('declaration_accepted', False)
        )
        return user


class UserLoginForm(forms.Form):
    email = forms.CharField(
        label="Email or Username",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'Enter your registered email or username'
        })
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'Enter your password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-brand-primary border-gray-300 rounded focus:ring-brand-primary'
        })
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar', 'agency_name', 'bio']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'block w-full text-xs text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-primary hover:file:bg-brand-100'
            }),
            'agency_name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
                'placeholder': 'Agency name (for brokers/agents)'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
                'rows': 3,
                'placeholder': 'Tell us about yourself or your real estate business'
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone:
            digits_only = ''.join(c for c in phone if c.isdigit())
            if len(digits_only) < 10 or len(digits_only) > 15:
                raise ValidationError("Please enter a valid 10-15 digit phone number.")
            if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
                raise ValidationError("This phone number is already registered to another account.")
        return phone


class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
                'placeholder': 'Enter your registered email address'
            })


class CustomSetPasswordForm(forms.Form):
    new_password1 = forms.CharField(
        label="New Password",
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'Enter new password'
        })
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'bg-gray-50 border border-gray-200 p-3 rounded-xl w-full text-xs font-bold text-gray-800 outline-none focus:border-brand-primary',
            'placeholder': 'Re-enter new password'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')

        if p1 and p2:
            if p1 != p2:
                self.add_error('new_password2', "Passwords do not match.")
            else:
                try:
                    validate_password(p1, user=self.user)
                except ValidationError as err:
                    self.add_error('new_password1', err)
        return cleaned_data

    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user
