from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone

def get_housing_sender():
    host_user = getattr(settings, 'EMAIL_HOST_USER', '').strip()
    if host_user:
        return f"Housing <{host_user}>"
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'Housing')

def send_housing_email(subject, template_name, context, recipient_email):
    sender = get_housing_sender()
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=sender,
        to=[recipient_email]
    )
    msg.attach_alternative(html_content, "text/html")
    return msg.send(fail_silently=False)

def send_registration_otp_email(name, recipient_email, otp_code):
    subject = "Verify your email address | Housing"
    context = {
        'name': name,
        'otp_code': otp_code,
    }
    return send_housing_email(subject, 'emails/registration_otp.html', context, recipient_email)

def send_login_otp_email(name, recipient_email, otp_code):
    subject = "Your login verification code | Housing"
    context = {
        'name': name,
        'otp_code': otp_code,
    }
    return send_housing_email(subject, 'emails/login_otp.html', context, recipient_email)

def send_property_interest_otp_email(name, recipient_email, otp_code, property_obj):
    subject = "Confirm your property enquiry | Housing"
    location = f"{property_obj.locality.name if property_obj.locality else ''}, {property_obj.city.name if property_obj.city else ''}".strip(', ')
    context = {
        'name': name,
        'otp_code': otp_code,
        'property_title': property_obj.title,
        'property_location': location or property_obj.address,
        'property_id': property_obj.id,
    }
    return send_housing_email(subject, 'emails/property_interest_otp.html', context, recipient_email)

def send_owner_enquiry_notification_email(owner_name, owner_email, buyer_name, buyer_email, buyer_phone, property_obj, message=""):
    subject = "New property enquiry received | Housing"
    location = f"{property_obj.locality.name if property_obj.locality else ''}, {property_obj.city.name if property_obj.city else ''}".strip(', ')
    context = {
        'owner_name': owner_name,
        'buyer_name': buyer_name,
        'buyer_email': buyer_email,
        'buyer_phone': buyer_phone,
        'property_title': property_obj.title,
        'property_id': property_obj.id,
        'property_location': location or property_obj.address,
        'enquiry_date': timezone.now().strftime("%d %B %Y, %I:%M %p"),
        'enquiry_message': message,
    }
    return send_housing_email(subject, 'emails/owner_property_enquiry_notification.html', context, owner_email)

def send_company_rental_agreement_notification_email(agreement_req):
    company_email = getattr(settings, 'EMAIL_HOST_USER', '').strip() or getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@housingclone.test').strip()
    subject = f"New Rental Agreement Request #{agreement_req.reference_number} | Housing"
    context = {
        'agreement': agreement_req,
        'submission_date': timezone.now().strftime("%d %B %Y, %I:%M %p"),
    }
    return send_housing_email(subject, 'emails/company_rental_agreement_notification.html', context, company_email)
