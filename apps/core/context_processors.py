def global_settings(request):
    """
    Global context processor injecting platform settings and brand constants into all Django templates.
    """
    return {
        'PLATFORM_NAME': 'HOUSING...',
        'PLATFORM_TAGLINE': 'India\'s Modern Real Estate Marketplace',
        'SUPPORT_EMAIL': 'support@housingclone.test',
        'SUPPORT_PHONE': '+91 1800 123 4567',
        'CURRENCY_SYMBOL': '₹',
    }
