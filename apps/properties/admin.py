from django.contrib import admin
from apps.properties.models import Property, PropertyType, Amenity, PropertyMedia, PropertyAmenity

class PropertyMediaInline(admin.TabularInline):
    model = PropertyMedia
    extra = 1

class PropertyAmenityInline(admin.TabularInline):
    model = PropertyAmenity
    extra = 1

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'city', 'locality', 'listing_purpose', 'price', 'bhk', 'listing_state', 'verification_state', 'created_at')
    list_filter = ('listing_purpose', 'listing_state', 'verification_state', 'property_type', 'city')
    search_fields = ('title', 'address', 'locality__name', 'city__name', 'owner__username')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PropertyMediaInline, PropertyAmenityInline]

@admin.register(PropertyType)
class PropertyTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug')
    prepopulated_fields = {'slug': ('name',)}
