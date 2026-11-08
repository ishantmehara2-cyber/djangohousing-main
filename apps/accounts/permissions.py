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
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff or user.is_admin_role:
        return True
    return property_obj.owner == user or property_obj.posted_by_user == user


def can_manage_lead(user, lead_obj):
    """
    Backend permission check: Returns True if agent/owner is assigned to the lead, or is admin.
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff or user.is_admin_role:
        return True
    return lead_obj.owner_user == user
