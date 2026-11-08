from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache

def invalidate_property_cache(sender, instance, **kwargs):
    cache.clear()

class PropertiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.properties'

    def ready(self):
        from apps.properties.models import Property
        post_save.connect(invalidate_property_cache, sender=Property)
        post_delete.connect(invalidate_property_cache, sender=Property)
