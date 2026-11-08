from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import home_view, health_check_view, robots_txt_view, sitemap_view
from apps.accounts.views import dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('health/', health_check_view, name='health_check'),
    path('robots.txt', robots_txt_view, name='robots_txt'),
    path('sitemap.xml', sitemap_view, name='sitemap_xml'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('admin-panel/', include('apps.moderation.urls')),
    path('', include('apps.core.urls')),
    path('', include('apps.billing.urls')),
    path('', include('apps.properties.urls')),
    path('', include('apps.accounts.urls')),
    path('', include('apps.engagements.urls')),
    path('services/', include('apps.services.urls')),
    path('', include('apps.locations.urls')),
    path('bank-loans/', include(('apps.services.urls', 'bank_loans_direct'), namespace='bank_loans_direct')),
    path('home-loan-calculator/', include(('apps.services.urls', 'calculator_direct'), namespace='calculator_direct')),
    path('rental-agreement/', include(('apps.services.urls', 'rental_direct'), namespace='rental_direct')),
]

handler400 = 'apps.core.views.custom_bad_request'
handler403 = 'apps.core.views.custom_permission_denied'
handler404 = 'apps.core.views.custom_page_not_found'
handler500 = 'apps.core.views.custom_server_error'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
