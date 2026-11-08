from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User, RoleChoices
from apps.accounts.permissions import admin_required
from apps.properties.models import Property, ListingStateChoices, PropertyFormField
from apps.engagements.models import Enquiry, PropertyVisit
from apps.moderation.models import AuditLog, Report, ReportStatusChoices, ReportReasonChoices

def render_admin_template(request, template_name, context):
    template = get_template(template_name)
    return HttpResponse(template.render(context, request))

@login_required
def admin_dashboard_overview_view(request):
    """Admin dashboard landing page with live database-driven statistics."""
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied: Administrator privileges required.")

    total_users = User.objects.count()
    buyers_count = User.objects.filter(role=RoleChoices.BUYER).count()
    tenants_count = User.objects.filter(role=RoleChoices.TENANT).count()
    owners_count = User.objects.filter(role=RoleChoices.OWNER).count()
    agents_count = User.objects.filter(role=RoleChoices.AGENT).count()
    admins_count = User.objects.filter(role=RoleChoices.ADMIN).count() + User.objects.filter(is_staff=True).count()

    total_properties = Property.objects.count()
    pending_properties_count = Property.objects.filter(listing_state=ListingStateChoices.PENDING_APPROVAL).count()
    active_properties = Property.objects.filter(listing_state=ListingStateChoices.ACTIVE).count()
    rejected_properties = Property.objects.filter(listing_state=ListingStateChoices.REJECTED).count()
    draft_properties = Property.objects.filter(listing_state=ListingStateChoices.DRAFT).count()
    sold_properties = Property.objects.filter(listing_state=ListingStateChoices.SOLD).count()
    rented_properties = Property.objects.filter(listing_state=ListingStateChoices.RENTED).count()

    total_enquiries = Enquiry.objects.count()
    total_visits = PropertyVisit.objects.count()

    recent_users = User.objects.order_by('-date_joined')[:5]
    pending_properties = Property.objects.filter(listing_state=ListingStateChoices.PENDING_APPROVAL).select_related('city', 'locality', 'owner')[:5]

    context = {
        'request': request,
        'user': request.user,
        'total_users': total_users,
        'buyers_count': buyers_count,
        'tenants_count': tenants_count,
        'owners_count': owners_count,
        'agents_count': agents_count,
        'admins_count': admins_count,
        'total_properties': total_properties,
        'pending_properties_count': pending_properties_count,
        'active_properties': active_properties,
        'rejected_properties': rejected_properties,
        'draft_properties': draft_properties,
        'sold_properties': sold_properties,
        'rented_properties': rented_properties,
        'total_enquiries': total_enquiries,
        'total_visits': total_visits,
        'recent_users': recent_users,
        'pending_properties': pending_properties,
    }
    return render_admin_template(request, 'admin_panel/dashboard.html', context)

@login_required
def admin_pending_properties_view(request):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    properties = Property.objects.filter(listing_state=ListingStateChoices.PENDING_APPROVAL).select_related('city', 'locality', 'property_type', 'owner')
    context = {'request': request, 'user': request.user, 'properties': properties}
    return render_admin_template(request, 'admin_panel/pending_properties.html', context)

@login_required
@transaction.atomic
def admin_approve_property_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    prop = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        prop.listing_state = ListingStateChoices.ACTIVE
        prop.verification_state = 'VERIFIED'
        prop.save(update_fields=['listing_state', 'verification_state'])
        AuditLog.objects.create(user=request.user, action='APPROVE_PROPERTY', entity='Property', entity_id=str(prop.id), payload={'title': prop.title})
        messages.success(request, f"Property '{prop.title}' has been successfully approved.")
    return redirect('moderation:pending-properties')

@login_required
@transaction.atomic
def admin_reject_property_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    prop = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', 'Did not meet standards.')
        prop.listing_state = ListingStateChoices.REJECTED
        prop.rejection_reason = reason
        prop.save(update_fields=['listing_state', 'rejection_reason'])
        AuditLog.objects.create(user=request.user, action='REJECT_PROPERTY', entity='Property', entity_id=str(prop.id), payload={'title': prop.title, 'reason': reason})
        messages.success(request, f"Property '{prop.title}' rejected.")
    return redirect('moderation:pending-properties')

@login_required
def admin_all_properties_view(request):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    properties = Property.objects.all().select_related('city', 'locality', 'property_type', 'owner')
    status_filter = request.GET.get('status')
    if status_filter:
        properties = properties.filter(listing_state=status_filter)
    context = {'request': request, 'user': request.user, 'properties': properties, 'selected_status': status_filter}
    return render_admin_template(request, 'admin_panel/all_properties.html', context)

@login_required
def admin_users_view(request):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    users = User.objects.all()
    role_filter = request.GET.get('role')
    if role_filter:
        users = users.filter(role=role_filter)
    context = {'request': request, 'user': request.user, 'users': users, 'selected_role': role_filter}
    return render_admin_template(request, 'admin_panel/users.html', context)

@login_required
@transaction.atomic
def admin_toggle_user_status_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, "Cannot deactivate your own account.")
        return redirect('moderation:users')
    if request.method == 'POST':
        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=['is_active'])
        AuditLog.objects.create(user=request.user, action='TOGGLE_USER_STATUS', entity='User', entity_id=str(target_user.id), payload={'username': target_user.username, 'is_active': target_user.is_active})
        messages.success(request, f"User {target_user.username} status updated.")
    return redirect('moderation:users')

@login_required
def admin_enquiries_view(request):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    enquiries = Enquiry.objects.all().select_related('property', 'sender_user')
    context = {'request': request, 'user': request.user, 'enquiries': enquiries}
    return render_admin_template(request, 'admin_panel/enquiries.html', context)

@login_required
def admin_visits_view(request):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    visits = PropertyVisit.objects.all().select_related('property', 'visitor_user')
    context = {'request': request, 'user': request.user, 'visits': visits}
    return render_admin_template(request, 'admin_panel/visits.html', context)

@login_required
def admin_reports_view(request):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    reports = Report.objects.all().select_related('property', 'reporter_user')
    context = {'request': request, 'user': request.user, 'reports': reports}
    return render_admin_template(request, 'admin_panel/reports.html', context)

@login_required
@transaction.atomic
def admin_resolve_report_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action', ReportStatusChoices.RESOLVED)
        notes = request.POST.get('investigation_notes', '')
        report.status = action
        report.investigation_notes = notes
        report.resolved_by_user = request.user
        report.resolved_at = timezone.now()
        report.save()
        AuditLog.objects.create(user=request.user, action='RESOLVE_REPORT', entity='Report', entity_id=str(report.id), payload={'action': action})
        messages.success(request, f"Report #{report.id} updated successfully.")
    return redirect('moderation:reports')

@login_required
def admin_audit_logs_view(request):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    logs = AuditLog.objects.all().select_related('user')[:100]
    context = {'request': request, 'user': request.user, 'logs': logs}
    return render_admin_template(request, 'admin_panel/audit_logs.html', context)

@login_required
def report_property_view(request, slug):
    prop = get_object_or_404(Property, slug=slug)
    if request.method == 'POST':
        reason_category = request.POST.get('reason_category', ReportReasonChoices.OTHER)
        reason = request.POST.get('reason', '')
        Report.objects.create(
            reporter_user=request.user,
            property=prop,
            reason_category=reason_category,
            reason=reason
        )
        messages.success(request, "Property successfully reported to platform moderators.")
    return redirect('properties:detail', slug=prop.slug)

@login_required
def admin_property_fields_management_view(request):
    if not (request.user.is_staff or request.user.is_superuser or request.user.is_admin_role):
        return HttpResponseForbidden("Access Denied.")
    fields = PropertyFormField.objects.all().prefetch_related('options')
    context = {
        'request': request,
        'user': request.user,
        'fields': fields,
    }
    return render_admin_template(request, 'admin_panel/property_fields.html', context)
