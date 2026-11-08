import time
from django.core.cache import cache
from django.http import HttpResponse

def rate_limit(max_attempts=15, window_seconds=60):
    """
    Rate limiting decorator restricting requests per IP address within a time window.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR', '127.0.0.1')
            cache_key = f"rate_limit_{view_func.__name__}_{ip}"

            attempts = cache.get(cache_key, 0)
            if attempts >= max_attempts:
                return HttpResponse("Too many requests. Please slow down and try again later.", status=429)

            cache.set(cache_key, attempts + 1, window_seconds)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
