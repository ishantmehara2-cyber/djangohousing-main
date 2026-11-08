import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone

from apps.accounts.models import RoleChoices, UserStatusChoices
from apps.accounts.forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserProfileForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm
)
from apps.accounts.permissions import (
    role_required,
    admin_required,
    can_manage_lead,
    user_has_role
)
from apps.core.rate_limiting import rate_limit
from apps.accounts.throttling import (
    is_login_throttled,
    record_failed_login,
    reset_login_attempts
)
from apps.services.models import EmailOTP, OTPPurposeChoices
from apps.services.email_service import (
    send_registration_otp_email,
    send_login_otp_email,
    send_property_interest_otp_email
)
from apps.properties.models import Property, ListingPurposeChoices
from apps.engagements.models import Favorite, Enquiry, Lead, PropertyVisit, LeadStatusChoices

User = get_user_model()


def get_dashboard_url_for_user(user):
    """
    Returns the role-specific dashboard URL for the given user.
    """
    if user.is_admin_role or user.is_staff or user.is_superuser:
        return reverse('accounts:admin_dashboard')
    elif user.role in [RoleChoices.AGENT, RoleChoices.DEVELOPER]:
        return reverse('accounts:agent_dashboard')
    elif user.role == RoleChoices.OWNER:
        return reverse('accounts:owner_dashboard')
    elif user.role == RoleChoices.TENANT:
        return reverse('accounts:tenant_dashboard')
    else:
        return reverse('accounts:buyer_dashboard')


def mask_email(email):
    if not email or '@' not in email:
        return email or '***'
    parts = email.split('@')
    name, domain = parts[0], parts[1]
    if len(name) <= 2:
        masked_name = name[0] + '*'
    else:
        masked_name = name[0] + '*' * (len(name) - 2) + name[-1]
    return f"{masked_name}@{domain}"


@rate_limit(max_attempts=10, window_seconds=60)
def register_view(request):
    """
    Handles new user registration with mandatory OTP verification.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            if User.objects.filter(email__iexact=cd['email']).exists():
                messages.error(request, "An account with this email address already exists. Please login instead.")
                return render(request, 'auth/register.html', {'form': form})

            request.session['pending_registration'] = {
                'first_name': cd['first_name'],
                'last_name': cd['last_name'],
                'email': cd['email'].lower().strip(),
                'phone': cd['phone'],
                'role': cd['role'],
                'password': cd['password'],
            }

            try:
                otp_obj, otp_code = EmailOTP.generate_otp(
                    email=cd['email'],
                    purpose=OTPPurposeChoices.REGISTER
                )
                send_registration_otp_email(cd['first_name'], cd['email'], otp_code)
                messages.info(request, f"A 6-digit verification code has been sent to {mask_email(cd['email'])}.")
                return redirect('accounts:verify_otp')
            except ValueError as ve:
                messages.warning(request, str(ve))
                return redirect('accounts:verify_otp')
            except Exception as e:
                messages.error(request, f"Error dispatching verification email: {e}")
        else:
            messages.error(request, "Please correct the errors below to complete registration.")
    else:
        form = UserRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


def verify_otp_view(request):
    """
    Renders Registration OTP entry screen and completes account activation upon successful verification.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    pending_data = request.session.get('pending_registration')
    if not pending_data:
        messages.warning(request, "No pending registration found. Please register your account.")
        return redirect('accounts:register')

    email = pending_data.get('email')

    if request.method == 'POST':
        user_otp = request.POST.get('otp', '').strip()
        otp_obj = EmailOTP.objects.filter(
            email__iexact=email,
            purpose=OTPPurposeChoices.REGISTER,
            is_verified=False
        ).order_by('-created_at').first()

        if not otp_obj:
            messages.error(request, "No active registration verification code found. Please click Resend Code.")
        else:
            is_valid, msg = otp_obj.verify(user_otp, expected_purpose=OTPPurposeChoices.REGISTER)
            if is_valid:
                # Create and activate user
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=pending_data['first_name'],
                    last_name=pending_data['last_name'],
                    phone=pending_data['phone'],
                    password=pending_data['password'],
                    role=pending_data['role'],
                    email_verified=True,
                    phone_verified=True,
                    is_active=True,
                    status=UserStatusChoices.ACTIVE
                )
                login(request, user)
                del request.session['pending_registration']
                messages.success(request, f"Welcome to Housing, {user.first_name}! Your email has been verified successfully.")
                return redirect(get_dashboard_url_for_user(user))
            else:
                messages.error(request, msg)

    return render(request, 'auth/verify_otp.html', {
        'masked_email': mask_email(email),
        'email': email,
    })


@rate_limit(max_attempts=10, window_seconds=60)
def login_view(request):
    """
    Step 1 of Two-Step Login: Validates credentials and initiates Two-Factor LOGIN OTP dispatch.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email_or_username = form.cleaned_data['email'].strip()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            throttled, remaining = is_login_throttled(request, identifier=email_or_username)
            if throttled:
                messages.error(request, f"Too many failed login attempts. Please try again in {remaining} seconds.")
                return render(request, 'auth/login.html', {'form': form})

            user = authenticate(request, username=email_or_username, password=password)
            if not user:
                try:
                    matched_user = User.objects.get(email__iexact=email_or_username)
                    user = authenticate(request, username=matched_user.username, password=password)
                except (User.DoesNotExist, User.MultipleObjectsReturned):
                    pass

            if user is not None and user.is_active:
                reset_login_attempts(request, identifier=email_or_username)

                # Store pending login session (Do NOT authenticate yet)
                request.session['pending_login_user_id'] = user.id
                request.session['pending_login_remember_me'] = remember_me
                request.session['pending_login_next_url'] = request.GET.get('next', '')

                try:
                    otp_obj, otp_code = EmailOTP.generate_otp(
                        email=user.email,
                        purpose=OTPPurposeChoices.LOGIN,
                        user=user
                    )
                    send_login_otp_email(user.first_name or user.username, user.email, otp_code)
                    messages.info(request, f"A 6-digit login verification code has been sent to {mask_email(user.email)}.")
                    return redirect('accounts:verify_login_otp')
                except ValueError as ve:
                    messages.warning(request, str(ve))
                    return redirect('accounts:verify_login_otp')
                except Exception as e:
                    messages.error(request, f"Error sending login verification email: {e}")
            else:
                record_failed_login(request, identifier=email_or_username)
                messages.error(request, "Invalid email address or password.")
        else:
            messages.error(request, "Please fill in all required fields correctly.")
    else:
        form = UserLoginForm()

    return render(request, 'auth/login.html', {'form': form})


def verify_login_otp_view(request):
    """
    Step 2 of Two-Step Login: Verifies LOGIN OTP before establishing authenticated session.
    """
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    user_id = request.session.get('pending_login_user_id')
    if not user_id:
        messages.warning(request, "No pending login session found. Please enter your credentials.")
        return redirect('accounts:login')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user_otp = request.POST.get('otp', '').strip()
        otp_obj = EmailOTP.objects.filter(
            email__iexact=user.email,
            purpose=OTPPurposeChoices.LOGIN,
            is_verified=False
        ).order_by('-created_at').first()

        if not otp_obj:
            messages.error(request, "No active login verification code found. Please click Resend Code.")
        else:
            is_valid, msg = otp_obj.verify(user_otp, expected_purpose=OTPPurposeChoices.LOGIN)
            if is_valid:
                login(request, user)

                remember_me = request.session.get('pending_login_remember_me', False)
                next_url = request.session.get('pending_login_next_url', '')

                if remember_me:
                    request.session.set_expiry(1209600)  # 2 weeks
                else:
                    request.session.set_expiry(0)

                # Clean up pending login session data
                for key in ['pending_login_user_id', 'pending_login_remember_me', 'pending_login_next_url']:
                    if key in request.session:
                        del request.session[key]

                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")

                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect(get_dashboard_url_for_user(user))
            else:
                messages.error(request, msg)

    return render(request, 'auth/verify_login_otp.html', {
        'masked_email': mask_email(user.email),
        'email': user.email,
    })


@require_POST
def resend_otp_view(request):
    """
    Resends OTP for active Registration or Login sessions with strict 60-second cooldown checks.
    """
    purpose = request.POST.get('purpose', OTPPurposeChoices.REGISTER)

    if purpose == OTPPurposeChoices.LOGIN:
        user_id = request.session.get('pending_login_user_id')
        if not user_id:
            messages.error(request, "No pending login session found.")
            return redirect('accounts:login')
        user = get_object_or_404(User, id=user_id)
        email = user.email
        name = user.first_name or user.username
    else:
        pending_data = request.session.get('pending_registration')
        if not pending_data:
            messages.error(request, "No pending registration session found.")
            return redirect('accounts:register')
        email = pending_data.get('email')
        name = pending_data.get('first_name', 'there')

    try:
        otp_obj, otp_code = EmailOTP.generate_otp(email=email, purpose=purpose)
        if purpose == OTPPurposeChoices.LOGIN:
            send_login_otp_email(name, email, otp_code)
            messages.success(request, "A new login verification code has been sent to your email address.")
            return redirect('accounts:verify_login_otp')
        else:
            send_registration_otp_email(name, email, otp_code)
            messages.success(request, "A new registration verification code has been sent to your email address.")
            return redirect('accounts:verify_otp')
    except ValueError as ve:
        messages.warning(request, str(ve))
        if purpose == OTPPurposeChoices.LOGIN:
            return redirect('accounts:verify_login_otp')
        return redirect('accounts:verify_otp')
    except Exception as e:
        messages.error(request, f"Error resending OTP code: {e}")
        if purpose == OTPPurposeChoices.LOGIN:
            return redirect('accounts:verify_login_otp')
        return redirect('accounts:verify_otp')


# ==============================================================================
# REST API ENDPOINTS FOR AUTHENTICATION & OTP WORKFLOWS
# ==============================================================================

@require_POST
def api_register_view(request):
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    password = data.get('password', '')
    role = data.get('role', RoleChoices.BUYER)

    if not first_name or not email or not password:
        return JsonResponse({'success': False, 'error': 'First name, email, and password are required.'}, status=400)

    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({'success': False, 'error': 'Account with this email already exists.'}, status=400)

    request.session['pending_registration'] = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'phone': phone,
        'role': role,
        'password': password,
    }

    try:
        otp_obj, otp_code = EmailOTP.generate_otp(email=email, purpose=OTPPurposeChoices.REGISTER)
        send_registration_otp_email(first_name, email, otp_code)
        return JsonResponse({
            'success': True,
            'message': 'Registration OTP sent successfully.',
            'masked_email': mask_email(email),
            'redirect_url': reverse('accounts:verify_otp')
        })
    except ValueError as ve:
        return JsonResponse({'success': False, 'error': str(ve)}, status=429)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to dispatch OTP email: {e}'}, status=500)


@require_POST
def api_verify_registration_otp_view(request):
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    email = data.get('email', '').strip().lower()
    otp_code = data.get('otp', '').strip()

    pending_data = request.session.get('pending_registration')
    if not pending_data or pending_data.get('email') != email:
        return JsonResponse({'success': False, 'error': 'No pending registration session found for this email.'}, status=400)

    otp_obj = EmailOTP.objects.filter(
        email__iexact=email,
        purpose=OTPPurposeChoices.REGISTER,
        is_verified=False
    ).order_by('-created_at').first()

    if not otp_obj:
        return JsonResponse({'success': False, 'error': 'No active verification code found.'}, status=400)

    is_valid, msg = otp_obj.verify(otp_code, expected_purpose=OTPPurposeChoices.REGISTER)
    if is_valid:
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=pending_data['first_name'],
            last_name=pending_data['last_name'],
            phone=pending_data['phone'],
            password=pending_data['password'],
            role=pending_data['role'],
            email_verified=True,
            phone_verified=True,
            is_active=True,
            status=UserStatusChoices.ACTIVE
        )
        login(request, user)
        del request.session['pending_registration']
        return JsonResponse({
            'success': True,
            'message': 'Email verified and account created successfully.',
            'redirect_url': get_dashboard_url_for_user(user)
        })
    else:
        return JsonResponse({'success': False, 'error': msg}, status=400)


@require_POST
def api_login_view(request):
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    email_or_username = data.get('email', '').strip()
    password = data.get('password', '')
    remember_me = data.get('remember_me', False)

    user = authenticate(request, username=email_or_username, password=password)
    if not user:
        try:
            matched_user = User.objects.get(email__iexact=email_or_username)
            user = authenticate(request, username=matched_user.username, password=password)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            pass

    if user is not None and user.is_active:
        request.session['pending_login_user_id'] = user.id
        request.session['pending_login_remember_me'] = remember_me

        try:
            otp_obj, otp_code = EmailOTP.generate_otp(
                email=user.email,
                purpose=OTPPurposeChoices.LOGIN,
                user=user
            )
            send_login_otp_email(user.first_name or user.username, user.email, otp_code)
            return JsonResponse({
                'success': True,
                'message': 'Login OTP dispatched successfully.',
                'masked_email': mask_email(user.email),
                'redirect_url': reverse('accounts:verify_login_otp')
            })
        except ValueError as ve:
            return JsonResponse({'success': False, 'error': str(ve)}, status=429)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Failed to dispatch login OTP: {e}'}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid email address or password.'}, status=400)


@require_POST
def api_verify_login_otp_view(request):
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    email = data.get('email', '').strip().lower()
    otp_code = data.get('otp', '').strip()

    user_id = request.session.get('pending_login_user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'No pending login session found.'}, status=400)

    user = get_object_or_404(User, id=user_id)
    if user.email.lower() != email:
        return JsonResponse({'success': False, 'error': 'Email mismatch for pending login session.'}, status=400)

    otp_obj = EmailOTP.objects.filter(
        email__iexact=email,
        purpose=OTPPurposeChoices.LOGIN,
        is_verified=False
    ).order_by('-created_at').first()

    if not otp_obj:
        return JsonResponse({'success': False, 'error': 'No active login OTP code found.'}, status=400)

    is_valid, msg = otp_obj.verify(otp_code, expected_purpose=OTPPurposeChoices.LOGIN)
    if is_valid:
        login(request, user)
        remember_me = request.session.get('pending_login_remember_me', False)
        if remember_me:
            request.session.set_expiry(1209600)
        else:
            request.session.set_expiry(0)

        for key in ['pending_login_user_id', 'pending_login_remember_me', 'pending_login_next_url']:
            if key in request.session:
                del request.session[key]

        return JsonResponse({
            'success': True,
            'message': 'Login successful.',
            'redirect_url': get_dashboard_url_for_user(user)
        })
    else:
        return JsonResponse({'success': False, 'error': msg}, status=400)


@require_POST
def api_resend_otp_view(request):
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    purpose = data.get('purpose', OTPPurposeChoices.REGISTER)

    if purpose == OTPPurposeChoices.LOGIN:
        user_id = request.session.get('pending_login_user_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'No pending login session.'}, status=400)
        user = get_object_or_404(User, id=user_id)
        email = user.email
        name = user.first_name or user.username
    else:
        pending_data = request.session.get('pending_registration')
        if not pending_data:
            return JsonResponse({'success': False, 'error': 'No pending registration session.'}, status=400)
        email = pending_data.get('email')
        name = pending_data.get('first_name', 'there')

    try:
        otp_obj, otp_code = EmailOTP.generate_otp(email=email, purpose=purpose)
        if purpose == OTPPurposeChoices.LOGIN:
            send_login_otp_email(name, email, otp_code)
        else:
            send_registration_otp_email(name, email, otp_code)

        return JsonResponse({'success': True, 'message': 'New verification OTP code sent successfully.'})
    except ValueError as ve:
        return JsonResponse({'success': False, 'error': str(ve)}, status=429)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to resend OTP: {e}'}, status=500)


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')


@login_required
def dashboard_view(request):
    return redirect(get_dashboard_url_for_user(request.user))


@login_required
@role_required(RoleChoices.BUYER, RoleChoices.TENANT_BUYER)
def buyer_dashboard_view(request):
    user = request.user
    favorites = Favorite.objects.filter(user=user).select_related('property', 'property__city', 'property__locality')
    enquiries = Enquiry.objects.filter(sender_user=user).select_related('property', 'property__city')
    visits = PropertyVisit.objects.filter(visitor_user=user).select_related('property')

    context = {
        'user': user,
        'favorites': favorites,
        'enquiries': enquiries,
        'visits': visits,
    }
    return render(request, 'dashboard/buyer_dashboard.html', context)


@login_required
@role_required(RoleChoices.TENANT, RoleChoices.TENANT_BUYER)
def tenant_dashboard_view(request):
    user = request.user
    favorites = Favorite.objects.filter(
        user=user,
        property__listing_purpose=ListingPurposeChoices.RENT
    ).select_related('property', 'property__city', 'property__locality')

    enquiries = Enquiry.objects.filter(
        sender_user=user,
        property__listing_purpose=ListingPurposeChoices.RENT
    ).select_related('property', 'property__city')

    visits = PropertyVisit.objects.filter(visitor_user=user).select_related('property')

    context = {
        'user': user,
        'favorites': favorites,
        'enquiries': enquiries,
        'visits': visits,
    }
    return render(request, 'dashboard/tenant_dashboard.html', context)


@login_required
@role_required(RoleChoices.OWNER)
def owner_dashboard_view(request):
    user = request.user
    properties = Property.objects.filter(posted_by_user=user).select_related('city', 'locality')
    leads = Lead.objects.filter(owner_user=user).select_related('property', 'lead_user')
    visits = PropertyVisit.objects.filter(property__posted_by_user=user).select_related('property', 'visitor_user')

    context = {
        'user': user,
        'properties': properties,
        'leads': leads,
        'visits': visits,
    }
    return render(request, 'dashboard/owner_dashboard.html', context)


@login_required
@role_required(RoleChoices.AGENT, RoleChoices.DEVELOPER)
def agent_dashboard_view(request):
    user = request.user
    properties = Property.objects.filter(posted_by_user=user).select_related('city', 'locality')
    leads = Lead.objects.filter(owner_user=user).select_related('property', 'lead_user')
    visits = PropertyVisit.objects.filter(property__posted_by_user=user).select_related('property', 'visitor_user')

    context = {
        'user': user,
        'properties': properties,
        'leads': leads,
        'visits': visits,
        'lead_statuses': LeadStatusChoices.choices,
    }
    return render(request, 'dashboard/agent_dashboard.html', context)


@login_required
@admin_required
def admin_dashboard_view(request):
    total_users = User.objects.count()
    total_properties = Property.objects.count()
    active_properties = Property.objects.filter(listing_state='ACTIVE').count()
    pending_properties = Property.objects.filter(listing_state='PENDING_VERIFICATION').count()
    total_enquiries = Enquiry.objects.count()

    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_properties = Property.objects.order_by('-created_at')[:10]

    context = {
        'total_users': total_users,
        'total_properties': total_properties,
        'active_properties': active_properties,
        'pending_properties': pending_properties,
        'total_enquiries': total_enquiries,
        'recent_users': recent_users,
        'recent_properties': recent_properties,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def profile_view(request):
    return render(request, 'auth/profile.html', {'user': request.user})


@login_required
def edit_profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'auth/edit_profile.html', {'form': form, 'user': user})


@login_required
@role_required(RoleChoices.AGENT, RoleChoices.OWNER, RoleChoices.ADMIN)
def update_lead_status_view(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    if not can_manage_lead(request.user, lead):
        messages.error(request, "You do not have permission to manage this lead.")
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(LeadStatusChoices.choices):
            lead.status = new_status
            lead.save()
            messages.success(request, f"Lead status updated to {lead.get_status_display()}.")

    return redirect('accounts:dashboard')
