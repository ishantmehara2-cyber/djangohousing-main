import json
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseForbidden, JsonResponse
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone

from apps.properties.models import Property, ListingStateChoices, PropertyType, ListingPurposeChoices, PropertyCategoryChoices, FurnishingChoices, PossessionStatusChoices
from apps.locations.models import City, Locality
from apps.billing.models import PropertyPromotion
from apps.engagements.models import (
    Favorite, Enquiry, Lead, PropertyVisit, Notification,
    LeadActivity, FollowUpReminder, LeadStatusChoices,
    UserPreference, RecentlyViewed, SavedSearch, PropertyPriceHistory
)
from apps.engagements.services.notifications import NotificationService
from apps.core.rate_limiting import rate_limit
from apps.services.models import EmailOTP, OTPPurposeChoices
from apps.services.email_service import (
    send_property_interest_otp_email,
    send_owner_enquiry_notification_email
)
from apps.properties.services.recommendation_service import PropertyRecommendationService


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


def render_engagement_template(request, template_name, context):
    context['request'] = request
    context['user'] = request.user
    template = get_template(template_name)
    return HttpResponse(template.render(context))


@login_required
def toggle_favorite_view(request, slug):
    property_item = get_object_or_404(Property, slug=slug)
    favorite, created = Favorite.objects.get_or_create(user=request.user, property=property_item)
    if not created:
        favorite.delete()
        messages.success(request, "Removed from saved properties.")
    else:
        messages.success(request, "Added to saved properties!")
    return redirect('properties:detail', slug=slug)


@login_required
@rate_limit(max_attempts=20, window_seconds=60)
def send_enquiry_view(request, slug):
    """
    Direct Property Interest Submission: Sends enquiry directly and notifies property owner via email.
    """
    property_item = get_object_or_404(Property, slug=slug)
    if request.method == 'POST':
        message_text = request.POST.get('message', "I'm interested in this property. Please contact me.").strip()
        user = request.user

        # Create Enquiry and Lead in database
        enquiry, created = Enquiry.objects.get_or_create(
            property=property_item,
            sender_user=user,
            defaults={'message': message_text}
        )
        if not created:
            enquiry.message = message_text
            enquiry.save()

        lead, _ = Lead.objects.get_or_create(
            property=property_item,
            lead_user=user,
            owner_user=property_item.owner,
            defaults={'notes': message_text, 'status': LeadStatusChoices.NEW}
        )

        LeadActivity.objects.create(
            lead=lead,
            actor_user=user,
            activity_type='ENQUIRY_CREATED',
            description=f"Direct Enquiry: {message_text}"
        )

        NotificationService.create_notification(
            user=property_item.owner,
            title=f"New Enquiry on {property_item.title}",
            message=f"User {user.get_full_name() or user.username} sent an enquiry: '{message_text}'"
        )

        # Directly dispatch email notification to Property Owner with buyer's Gmail & Phone Number
        try:
            send_owner_enquiry_notification_email(
                owner_name=property_item.owner.get_full_name() or property_item.owner.username,
                owner_email=property_item.owner.email,
                buyer_name=user.get_full_name() or user.username,
                buyer_email=user.email,
                buyer_phone=user.phone or 'Not Provided',
                property_obj=property_item,
                message=message_text
            )
        except Exception:
            pass

        messages.success(
            request,
            f"Your interest in '{property_item.title}' has been sent to the owner! "
            f"Your contact details ({user.email} & {user.phone or 'Phone'}) have been shared with {property_item.owner.get_full_name() or property_item.owner.username}."
        )

    return redirect('properties:detail', slug=slug)


@login_required
def verify_property_interest_otp_view(request, pk):
    """
    Legacy/Optional OTP Verification fallback endpoint for property interest.
    """
    property_item = get_object_or_404(Property, pk=pk)
    user = request.user
    message_text = request.session.get(f'pending_enquiry_msg_{property_item.id}', "I'm interested in this property. Please contact me.")

    if request.method == 'POST':
        user_otp = request.POST.get('otp', '').strip()
        otp_obj = EmailOTP.objects.filter(
            email__iexact=user.email,
            purpose=OTPPurposeChoices.PROPERTY_INTEREST,
            property=property_item,
            is_verified=False
        ).order_by('-created_at').first()

        if not otp_obj:
            messages.error(request, "No active confirmation code found. Please click Resend Code.")
        else:
            is_valid, msg = otp_obj.verify(
                user_otp,
                expected_purpose=OTPPurposeChoices.PROPERTY_INTEREST,
                expected_property_id=property_item.id
            )
            if is_valid:
                enquiry, created = Enquiry.objects.get_or_create(
                    property=property_item,
                    sender_user=user,
                    defaults={'message': message_text}
                )
                if not created:
                    enquiry.message = message_text
                    enquiry.save()

                lead, _ = Lead.objects.get_or_create(
                    property=property_item,
                    lead_user=user,
                    owner_user=property_item.owner,
                    defaults={'notes': message_text, 'status': LeadStatusChoices.NEW}
                )

                try:
                    send_owner_enquiry_notification_email(
                        owner_name=property_item.owner.get_full_name() or property_item.owner.username,
                        owner_email=property_item.owner.email,
                        buyer_name=user.get_full_name() or user.username,
                        buyer_email=user.email,
                        buyer_phone=user.phone or 'Not Provided',
                        property_obj=property_item,
                        message=message_text
                    )
                except Exception:
                    pass

                messages.success(request, "Your enquiry has been verified and delivered to the property owner successfully!")
                return redirect('properties:detail', slug=property_item.slug)
            else:
                messages.error(request, msg)

    location = f"{property_item.locality.name if property_item.locality else ''}, {property_item.city.name if property_item.city else ''}".strip(', ')
    context = {
        'property_item': property_item,
        'property_location': location or property_item.address,
        'masked_email': mask_email(user.email),
    }
    return render(request, 'engagements/verify_property_interest_otp.html', context)


@login_required
@require_POST
def resend_property_interest_otp_view(request, pk):
    property_item = get_object_or_404(Property, pk=pk)
    try:
        otp_obj, otp_code = EmailOTP.generate_otp(
            email=request.user.email,
            purpose=OTPPurposeChoices.PROPERTY_INTEREST,
            user=request.user,
            property_obj=property_item
        )
        send_property_interest_otp_email(
            request.user.first_name or request.user.username,
            request.user.email,
            otp_code,
            property_item
        )
        messages.success(request, "A new property interest confirmation code has been sent to your email.")
    except ValueError as ve:
        messages.warning(request, str(ve))
    except Exception as e:
        messages.error(request, f"Error resending code: {e}")

    return redirect('engagements:verify-property-interest-otp', pk=property_item.id)


@login_required
@require_POST
def api_express_property_interest_view(request, pk):
    """
    API endpoint for direct property interest submission and immediate owner notification.
    """
    property_item = get_object_or_404(Property, pk=pk)
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    message_text = data.get('message', "I'm interested in this property. Please contact me.").strip()
    user = request.user

    enquiry, created = Enquiry.objects.get_or_create(
        property=property_item,
        sender_user=user,
        defaults={'message': message_text}
    )
    if not created:
        enquiry.message = message_text
        enquiry.save()

    lead, _ = Lead.objects.get_or_create(
        property=property_item,
        lead_user=user,
        owner_user=property_item.owner,
        defaults={'notes': message_text, 'status': LeadStatusChoices.NEW}
    )

    try:
        send_owner_enquiry_notification_email(
            owner_name=property_item.owner.get_full_name() or property_item.owner.username,
            owner_email=property_item.owner.email,
            buyer_name=user.get_full_name() or user.username,
            buyer_email=user.email,
            buyer_phone=user.phone or 'Not Provided',
            property_obj=property_item,
            message=message_text
        )
    except Exception:
        pass

    return JsonResponse({
        'success': True,
        'message': 'Your interest has been sent to the property owner directly with your contact details.',
        'property_id': property_item.id,
        'owner_notified': True
    })


@login_required
@require_POST
def api_verify_property_interest_otp_view(request, pk):
    property_item = get_object_or_404(Property, pk=pk)
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else request.POST
    except Exception:
        data = request.POST

    otp_code = data.get('otp', '').strip()
    message_text = request.session.get(f'pending_enquiry_msg_{property_item.id}', "I'm interested in this property. Please contact me.")

    otp_obj = EmailOTP.objects.filter(
        email__iexact=request.user.email,
        purpose=OTPPurposeChoices.PROPERTY_INTEREST,
        property=property_item,
        is_verified=False
    ).order_by('-created_at').first()

    if not otp_obj:
        return JsonResponse({'success': False, 'error': 'No active confirmation code found.'}, status=400)

    is_valid, msg = otp_obj.verify(
        otp_code,
        expected_purpose=OTPPurposeChoices.PROPERTY_INTEREST,
        expected_property_id=property_item.id
    )

    if is_valid:
        enquiry, created = Enquiry.objects.get_or_create(
            property=property_item,
            sender_user=request.user,
            defaults={'message': message_text}
        )
        if not created:
            enquiry.message = message_text
            enquiry.save()

        lead, _ = Lead.objects.get_or_create(
            property=property_item,
            lead_user=request.user,
            owner_user=property_item.owner,
            defaults={'notes': message_text, 'status': LeadStatusChoices.NEW}
        )

        try:
            send_owner_enquiry_notification_email(
                owner_name=property_item.owner.get_full_name() or property_item.owner.username,
                owner_email=property_item.owner.email,
                buyer_name=request.user.get_full_name() or request.user.username,
                buyer_email=request.user.email,
                buyer_phone=request.user.phone or 'Not Provided',
                property_obj=property_item,
                message=message_text
            )
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'message': 'Enquiry verified and sent to property owner successfully.'
        })
    else:
        return JsonResponse({'success': False, 'error': msg}, status=400)


@login_required
@rate_limit(max_attempts=20, window_seconds=60)
def schedule_visit_view(request, slug):
    property_item = get_object_or_404(Property, slug=slug)
    if request.method == 'POST':
        date_str = request.POST.get('visit_date')
        time_str = request.POST.get('visit_time', '10:00')
        notes = request.POST.get('notes', '')

        if date_str:
            try:
                dt_str = f"{date_str} {time_str}"
                visit_dt = datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
                if visit_dt < datetime.datetime.now():
                    messages.error(request, "Cannot schedule a property visit in the past.")
                else:
                    visit = PropertyVisit.objects.create(
                        property=property_item,
                        visitor_user=request.user,
                        visit_date=visit_dt,
                        notes=notes,
                        status='SCHEDULED'
                    )

                    NotificationService.create_notification(
                        user=property_item.owner,
                        title=f"Site Visit Requested for {property_item.title}",
                        message=f"User {request.user.username} requested a property visit on {visit_dt.strftime('%B %d, %Y at %H:%M')}."
                    )

                    messages.success(request, "Property visit scheduled successfully! Awaiting owner/agent confirmation.")
            except ValueError:
                messages.error(request, "Invalid date or time format.")
    return redirect('properties:detail', slug=slug)


@login_required
def notifications_list_view(request):
    notifications = Notification.objects.filter(user=request.user)
    context = {'notifications': notifications}
    return render_engagement_template(request, 'notifications/notification_list.html', context)


@login_required
def mark_notification_read_view(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return redirect('engagements:notifications')


@login_required
def mark_all_notifications_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('engagements:notifications')


@login_required
def buyer_enquiries_view(request):
    enquiries = Enquiry.objects.filter(sender_user=request.user).select_related('property', 'property__city')
    visits = PropertyVisit.objects.filter(visitor_user=request.user).select_related('property')
    context = {'enquiries': enquiries, 'visits': visits}
    return render_engagement_template(request, 'crm/buyer_enquiries.html', context)


@login_required
def owner_enquiries_view(request):
    leads = Lead.objects.filter(owner_user=request.user).select_related('property', 'lead_user')
    visits = PropertyVisit.objects.filter(property__posted_by_user=request.user).select_related('property', 'visitor_user')
    context = {'leads': leads, 'visits': visits}
    return render_engagement_template(request, 'crm/owner_enquiries.html', context)


@login_required
def user_preferences_view(request):
    pref, _ = UserPreference.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        pref.purpose = request.POST.get('purpose', pref.purpose)
        pref.city_id = request.POST.get('city') or None
        pref.locality_id = request.POST.get('locality') or None
        pref.property_type_id = request.POST.get('property_type') or None
        pref.min_price = request.POST.get('min_price') or None
        pref.max_price = request.POST.get('max_price') or None
        pref.min_bhk = request.POST.get('min_bhk') or None
        pref.max_bhk = request.POST.get('max_bhk') or None
        pref.furnishing = request.POST.get('furnishing') or None
        pref.save()
        messages.success(request, "Preferences saved successfully.")
        return redirect('engagements:preferences')
    cities = City.objects.filter(is_active=True)
    localities = Locality.objects.filter(is_active=True)
    property_types = PropertyType.objects.all()
    context = {
        'preference': pref,
        'purposes': ListingPurposeChoices.choices,
        'cities': cities,
        'localities': localities,
        'property_types': property_types,
        'furnishing_choices': FurnishingChoices.choices,
    }
    return render_engagement_template(request, 'crm/preferences.html', context)


@login_required
def recently_viewed_view(request):
    items = RecentlyViewed.objects.filter(user=request.user).select_related('property')
    context = {'recently_viewed': items}
    return render_engagement_template(request, 'crm/recently_viewed.html', context)


@login_required
def clear_recently_viewed_view(request):
    RecentlyViewed.objects.filter(user=request.user).delete()
    messages.success(request, "Viewed history cleared.")
    return redirect('engagements:recently-viewed')


@login_required
def saved_searches_view(request):
    searches = SavedSearch.objects.filter(user=request.user)
    context = {'saved_searches': searches}
    return render_engagement_template(request, 'crm/saved_searches.html', context)


@login_required
def save_current_search_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', 'Saved Search')
        criteria = dict(request.POST)
        SavedSearch.objects.create(user=request.user, name=name, search_criteria=criteria)
        messages.success(request, "Search saved successfully.")
    return redirect('engagements:saved-searches')


@login_required
def delete_saved_search_view(request, pk):
    search = get_object_or_404(SavedSearch, pk=pk, user=request.user)
    search.delete()
    messages.success(request, "Saved search deleted.")
    return redirect('engagements:saved-searches')


@login_required
def smart_discover_dashboard_view(request):
    pref = getattr(request.user, 'preference_profile', None)
    recommendations = PropertyRecommendationService.get_recommendations_for_user(request.user)
    context = {'preference': pref, 'recommendations': recommendations}
    return render_engagement_template(request, 'crm/smart_discover.html', context)
