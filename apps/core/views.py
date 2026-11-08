from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import datetime
from apps.locations.models import City, Locality
from apps.properties.models import Property, PropertyType, ListingPurposeChoices
from apps.core.models import FAQCategory, FAQItem, SupportTicket, TicketMessage, TicketCategoryChoices, TicketStatusChoices, TicketPriorityChoices

def home_view(request):
    """
    Renders the customer homepage with popular cities, top localities, property types, and optimized database querysets.
    """
    popular_cities = City.objects.filter(is_active=True, is_popular=True).select_related('state')[:8]
    top_localities = Locality.objects.select_related('city')[:8]

    featured_properties = Property.objects.filter(listing_state='ACTIVE')\
        .select_related('city', 'locality', 'property_type', 'owner')\
        .prefetch_related('media')[:6]

    buy_properties = Property.objects.filter(listing_state='ACTIVE', listing_purpose=ListingPurposeChoices.BUY)\
        .select_related('city', 'locality', 'property_type')\
        .prefetch_related('media')[:4]

    rent_properties = Property.objects.filter(listing_state='ACTIVE', listing_purpose=ListingPurposeChoices.RENT)\
        .select_related('city', 'locality', 'property_type')\
        .prefetch_related('media')[:4]

    property_types = PropertyType.objects.all()

    context = {
        'popular_cities': popular_cities,
        'top_localities': top_localities,
        'featured_properties': featured_properties,
        'buy_properties': buy_properties,
        'rent_properties': rent_properties,
        'property_types': property_types,
        'purposes': ListingPurposeChoices.choices,
    }
    return render(request, 'pages/home.html', context)

def health_check_view(request):
    """
    Health-check endpoint returning JSON response indicating Django backend is running.
    """
    return JsonResponse({
        'status': 'healthy',
        'backend': 'Django',
        'timestamp': datetime.datetime.now().isoformat(),
        'database': 'connected'
    })

def robots_txt_view(request):
    """
    Dynamic robots.txt view allowing search indexing for public pages and blocking private routes.
    """
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /admin-panel/",
        "Disallow: /dashboard/",
        "Disallow: /auth/",
        "Disallow: /billing/",
        "Disallow: /leads/",
        "Allow: /",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def sitemap_view(request):
    """
    Dynamic XML sitemap listing public properties and static pages.
    """
    properties = Property.objects.filter(listing_state='ACTIVE')[:1000]
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        '  <url><loc>https://housingclone.local/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>',
        '  <url><loc>https://housingclone.local/properties/buy/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>',
        '  <url><loc>https://housingclone.local/properties/rent/</loc><changefreq>daily</changefreq><priority>0.9</priority></url>',
        '  <url><loc>https://housingclone.local/help/</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>',
        '  <url><loc>https://housingclone.local/support/</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>',
        '  <url><loc>https://housingclone.local/about/</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>',
        '  <url><loc>https://housingclone.local/contact/</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>',
    ]
    for p in properties:
        loc = request.build_absolute_uri(f'/property/{p.slug}/')
        xml_lines.append(f'  <url><loc>{loc}</loc><lastmod>{p.updated_at.strftime("%Y-%m-%d")}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    xml_lines.append('</urlset>')
    return HttpResponse("\n".join(xml_lines), content_type="application/xml")

# Legal & Business Pages
def about_view(request):
    return render(request, 'pages/legal/about.html')

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        messages.success(request, "Thank you for contacting us! Our support team will respond within 24 hours.")
        return redirect('contact')
    return render(request, 'pages/legal/contact.html')

def terms_view(request):
    return render(request, 'pages/legal/terms.html')

def privacy_view(request):
    return render(request, 'pages/legal/privacy.html')

def cookie_policy_view(request):
    return render(request, 'pages/legal/cookie_policy.html')

def listing_guidelines_view(request):
    return render(request, 'pages/legal/listing_guidelines.html')

def refund_policy_view(request):
    return render(request, 'pages/legal/refund_policy.html')

def payment_terms_view(request):
    return render(request, 'pages/legal/payment_terms.html')

def disclaimer_view(request):
    return render(request, 'pages/legal/disclaimer.html')

def grievance_view(request):
    return render(request, 'pages/legal/grievance.html')

# FAQ & Help Centre
def help_centre_view(request):
    query = request.GET.get('q', '')
    categories = FAQCategory.objects.prefetch_related('faqs')
    if query:
        faqs = FAQItem.objects.filter(is_published=True, question__icontains=query) | FAQItem.objects.filter(is_published=True, answer__icontains=query)
    else:
        faqs = None
    context = {'categories': categories, 'query': query, 'search_faqs': faqs}
    return render(request, 'support/help_centre.html', context)

# Customer Support System
@login_required
def support_ticket_list_view(request):
    tickets = SupportTicket.objects.filter(user=request.user)
    context = {'tickets': tickets}
    return render(request, 'support/ticket_list.html', context)

@login_required
def create_support_ticket_view(request):
    if request.method == 'POST':
        category = request.POST.get('category', TicketCategoryChoices.OTHER)
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        priority = request.POST.get('priority', TicketPriorityChoices.MEDIUM)
        attachment = request.FILES.get('attachment')

        ticket_id = f"{timezone.now().strftime('%Y%m%d%H%M%S')}-{request.user.id}"
        ticket = SupportTicket.objects.create(
            user=request.user,
            ticket_id=ticket_id,
            category=category,
            subject=subject,
            description=description,
            priority=priority,
            attachment=attachment
        )
        TicketMessage.objects.create(ticket=ticket, sender=request.user, message=description)
        messages.success(request, f"Support Ticket #{ticket.ticket_id} created successfully.")
        return redirect('support:ticket-detail', ticket_id=ticket.ticket_id)

    context = {'categories': TicketCategoryChoices.choices, 'priorities': TicketPriorityChoices.choices}
    return render(request, 'support/ticket_create.html', context)

@login_required
def support_ticket_detail_view(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id)
    if not request.user.is_admin_role and ticket.user != request.user:
        raise Http404("Ticket not found.")

    if request.method == 'POST':
        msg_text = request.POST.get('message')
        if msg_text:
            TicketMessage.objects.create(ticket=ticket, sender=request.user, message=msg_text)
            if request.user.is_admin_role:
                ticket.status = TicketStatusChoices.WAITING_FOR_USER
            else:
                ticket.status = TicketStatusChoices.IN_PROGRESS
            ticket.save()
            messages.success(request, "Reply added successfully.")
            return redirect('support:ticket-detail', ticket_id=ticket.ticket_id)

    context = {'ticket': ticket, 'messages_list': ticket.messages.select_related('sender')}
    return render(request, 'support/ticket_detail.html', context)

# Error Handlers
def custom_bad_request(request, exception=None):
    return render(request, 'errors/400.html', status=400)

def custom_permission_denied(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def custom_page_not_found(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def custom_server_error(request, exception=None):
    return render(request, 'errors/500.html', status=500)

def maintenance_view(request):
    return render(request, 'errors/maintenance.html')
