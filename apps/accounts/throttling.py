import time
from django.core.cache import cache

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 300  # 5 minutes lockout

def get_client_ip(request):
    """
    Extracts client IP address from HTTP headers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip

def is_login_throttled(request, identifier=""):
    """
    Checks if login attempts for IP or identifier have exceeded maximum threshold.
    Returns (is_throttled: bool, remaining_seconds: int)
    """
    ip = get_client_ip(request)
    cache_key = f"login_attempts_{ip}_{identifier.lower()}"
    lockout_key = f"login_lockout_{ip}_{identifier.lower()}"

    lockout_until = cache.get(lockout_key)
    if lockout_until:
        remaining = int(lockout_until - time.time())
        if remaining > 0:
            return True, remaining
        else:
            cache.delete(lockout_key)
            cache.delete(cache_key)

    return False, 0

def record_failed_login(request, identifier=""):
    """
    Increments failed login counter and triggers lockout if threshold reached.
    """
    ip = get_client_ip(request)
    cache_key = f"login_attempts_{ip}_{identifier.lower()}"
    lockout_key = f"login_lockout_{ip}_{identifier.lower()}"

    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, LOCKOUT_DURATION_SECONDS)

    if attempts >= MAX_LOGIN_ATTEMPTS:
        lockout_until = time.time() + LOCKOUT_DURATION_SECONDS
        cache.set(lockout_key, lockout_until, LOCKOUT_DURATION_SECONDS)

def reset_login_attempts(request, identifier=""):
    """
    Clears failed login attempts after successful login.
    """
    ip = get_client_ip(request)
    cache_key = f"login_attempts_{ip}_{identifier.lower()}"
    lockout_key = f"login_lockout_{ip}_{identifier.lower()}"
    cache.delete(cache_key)
    cache.delete(lockout_key)
