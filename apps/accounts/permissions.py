from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from apps.accounts.models import RoleChoices

def user_has_role(user, allowed_roles):
    """
    Checks if a user is authenticated and possesses one of the allowed roles,
    or is a superuser/staff if admin role is allowed.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True

    # Map aliases / checks
    user_roles = {user.role}
    if user.role == RoleChoices.TENANT_BUYER:
        user_roles.add(RoleChoices.BUYER)
        user_roles.add(RoleChoices.TENANT)

    for role in allowed_roles:
        if role in user_roles:
            return True
    return False


def role_required(*allowed_roles, redirect_url='accounts:dashboard'):
    """
    Decorator to restrict view access to specific user roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')

            if user_has_role(request.user, allowed_roles):
                return view_func(request, *args, **kwargs)

            messages.error(request, "Access denied: You do not have permission to view this section.")
            return redirect(redirect_url)
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """
    Decorator for administrative views.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.is_admin_role or request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.error(request, "Access restricted to platform administrators.")
        return redirect('accounts:dashboard')
    return _wrapped_view


class RoleRequiredMixin:
    """
    Mixin for class-based views to enforce role-based authorization.
    """
    allowed_roles = []
    permission_denied_redirect = 'accounts:dashboard'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not user_has_role(request.user, self.allowed_roles):
            messages.error(request, "Access denied: You do not have permission to view this page.")
            return redirect(self.permission_denied_redirect)
        return super().dispatch(request, *args, **kwargs)


def can_edit_property(user, property_obj):
    """
    Backend permission check: Returns True if user owns or posted the property, or is admin.
    Must also be an approved partner or admin.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff or user.is_admin_role:
        return True
    if not user.is_approved_partner:
        return False
    return property_obj.owner == user or property_obj.posted_by_user == user


def can_post_property(user):
    """
    Strict backend permission check for property posting & editing:
    Only approved Real Estate Partners (and platform admins) have posting privileges.
    Customers, pending partners, rejected partners, and suspended accounts cannot post properties.
    """
    if not user or not user.is_authenticated:
        return False, "Authentication required to post property listings."
    if user.is_superuser or user.is_staff or user.is_admin_role:
        return True, "Admin privilege granted."
    if user.is_customer_account:
        return False, "Customer accounts are not permitted to post properties. Please register as a Real Estate Partner."
    if user.is_real_estate_partner:
        status = getattr(user, 'partner_approval_status', 'PENDING')
        if status == 'APPROVED':
            return True, "Approved Real Estate Partner."
        elif status == 'PENDING':
            return False, "Your Real Estate Partner application is pending admin verification."
        elif status == 'UNDER_VERIFICATION':
            return False, "Your Real Estate Partner application is currently under verification by our team."
        elif status == 'REJECTED':
            reason = f" Reason: {user.partner_rejection_reason}" if getattr(user, 'partner_rejection_reason', None) else ""
            return False, f"Your Real Estate Partner application was rejected.{reason}"
        elif status == 'ADDITIONAL_DOCS_REQUIRED':
            return False, "Additional verification documents are required for your Real Estate Partner account."
        else:
            return False, "Your account is not approved to post property listings."
    return False, "You do not have property posting privileges."


def approved_partner_required(view_func):
    """
    Decorator to restrict view access strictly to approved Real Estate Partners and Admins.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        can_post, msg = can_post_property(request.user)
        if can_post:
            return view_func(request, *args, **kwargs)
        messages.error(request, msg)
        return redirect('accounts:dashboard')
    return _wrapped_view


def can_manage_lead(user, lead_obj):
    """
    Backend permission check: Returns True if agent/owner is assigned to the lead, or is admin.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff or user.is_admin_role:
        return True
    return lead_obj.owner_user == user
