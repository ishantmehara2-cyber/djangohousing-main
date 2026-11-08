from django.contrib.sitemaps import Sitemap
from apps.properties.models import Property

class PropertySitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.8

    def items(self):
        return Property.objects.public().select_related('city', 'locality')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f"/property/{obj.slug}/"

class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        return [
            'home',
            'properties:buy',
            'properties:rent',
            'properties:commercial',
            'properties:search',
            'billing:pricing',
        ]

    def location(self, item):
        from django.urls import reverse
        return reverse(item)
