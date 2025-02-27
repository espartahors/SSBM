# users/decorators.py

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from functools import wraps

def role_required(role):
    """
    Decorator for views that checks whether a user has a particular role,
    redirecting to the login page if necessary.
    """
    def check_role(user):
        return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == role
    return user_passes_test(check_role)

def admin_required(function):
    """Decorator for views that require admin role"""
    return role_required('admin')(function)

def manager_required(function):
    """Decorator for views that require manager role or higher"""
    def check_manager_or_admin(user):
        return user.is_authenticated and hasattr(user, 'profile') and user.profile.role in ['admin', 'manager']
    return user_passes_test(check_manager_or_admin)(function)

def permission_required(permission_name):
    """
    Decorator for views that checks whether a user has a particular permission,
    redirecting to the login page if necessary.
    
    Permission name should be one of:
    - can_add_parts
    - can_edit_parts
    - can_delete_parts
    - can_view_documents
    - can_add_documents
    - can_upload_csv
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not hasattr(request.user, 'profile'):
                return HttpResponseForbidden("User profile not found. Please contact an administrator.")
            
            if not getattr(request.user.profile, permission_name, False):
                return HttpResponseForbidden(f"You don't have permission to access this feature.")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def can_add_parts(function):
    """Decorator for views that require add parts permission"""
    return permission_required('can_add_parts')(function)

def can_edit_parts(function):
    """Decorator for views that require edit parts permission"""
    return permission_required('can_edit_parts')(function)

def can_delete_parts(function):
    """Decorator for views that require delete parts permission"""
    return permission_required('can_delete_parts')(function)

def can_view_documents(function):
    """Decorator for views that require view documents permission"""
    return permission_required('can_view_documents')(function)

def can_add_documents(function):
    """Decorator for views that require add documents permission"""
    return permission_required('can_add_documents')(function)

def can_upload_csv(function):
    """Decorator for views that require CSV upload permission"""
    return permission_required('can_upload_csv')(function)