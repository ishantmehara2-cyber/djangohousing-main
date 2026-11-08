from django.contrib import admin
from apps.locations.models import Country, State, District, City, Locality, SubLocality

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_code', 'is_active')
    search_fields = ('name', 'iso_code')

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name', 'state_code', 'district_count', 'country', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'state_code', 'lgd_code')
    readonly_fields = ('lgd_code',)

    def district_count(self, obj):
        return obj.districts.count()
    district_count.short_description = 'Districts'

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'lgd_code', 'is_active')
    list_filter = ('state', 'is_active')
    search_fields = ('name', 'state__name', 'lgd_code')
    autocomplete_fields = ('state',)
    readonly_fields = ('lgd_code',)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'state', 'city_type', 'is_popular', 'is_active', 'lgd_code')
    list_filter = ('state', 'city_type', 'is_popular', 'is_active')
    search_fields = ('name', 'district__name', 'state__name', 'lgd_code')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('lgd_code',)

@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'pincode', 'is_active')
    list_filter = ('city__state', 'city', 'is_active')
    search_fields = ('name', 'city__name', 'pincode')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(SubLocality)
class SubLocalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'locality', 'pincode', 'is_active')
    list_filter = ('locality__city__state', 'locality__city', 'is_active')
    search_fields = ('name', 'locality__name', 'pincode')
    prepopulated_fields = {'slug': ('name',)}
