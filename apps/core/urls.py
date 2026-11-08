from django.urls import path
from apps.core.views import (
    about_view, contact_view, terms_view, privacy_view, cookie_policy_view,
    listing_guidelines_view, refund_policy_view, payment_terms_view, disclaimer_view, grievance_view,
    help_centre_view, support_ticket_list_view, create_support_ticket_view, support_ticket_detail_view,
    health_check_view, robots_txt_view, sitemap_view, maintenance_view
)
from apps.brokers.views import brokers_list_view
from apps.projects.views import projects_list_view, project_detail_view

app_name = 'support'

urlpatterns = [
    path('about/', about_view, name='about'),
    path('contact/', contact_view, name='contact'),
    path('terms/', terms_view, name='terms'),
    path('privacy/', privacy_view, name='privacy'),
    path('cookie-policy/', cookie_policy_view, name='cookie-policy'),
    path('listing-guidelines/', listing_guidelines_view, name='listing-guidelines'),
    path('refund-policy/', refund_policy_view, name='refund-policy'),
    path('payment-terms/', payment_terms_view, name='payment-terms'),
    path('disclaimer/', disclaimer_view, name='disclaimer'),
    path('grievance/', grievance_view, name='grievance'),

    path('help/', help_centre_view, name='help-centre'),
    path('support/', support_ticket_list_view, name='support-list'),
    path('support/new/', create_support_ticket_view, name='support-create'),
    path('support/<str:ticket_id>/', support_ticket_detail_view, name='ticket-detail'),

    path('brokers/', brokers_list_view, name='brokers-list'),
    path('projects/', projects_list_view, name='projects-list'),
    path('projects/<slug:slug>/', project_detail_view, name='project-detail'),

    path('api/health/', health_check_view, name='health-check'),
    path('robots.txt', robots_txt_view, name='robots-txt'),
    path('sitemap.xml', sitemap_view, name='sitemap-xml'),
    path('maintenance/', maintenance_view, name='maintenance'),
]
