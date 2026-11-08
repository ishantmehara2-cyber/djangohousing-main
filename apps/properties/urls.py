from django.urls import path
from apps.properties.views import (
    property_list_view,
    buy_property_list_view,
    rent_property_list_view,
    commercial_property_list_view,
    residential_property_list_view,
    property_search_view,
    property_detail_view,
    property_compare_view,
    post_property_view,
    edit_property_view,
    my_properties_view
)
from apps.properties.api_views import (
    api_property_fields_list,
    api_admin_property_fields,
    api_admin_property_field_detail,
    api_admin_property_field_status,
    api_admin_property_fields_reorder,
    api_admin_property_field_options,
)

app_name = 'properties'

urlpatterns = [
    path('properties/', property_list_view, name='list'),
    path('properties/buy/', buy_property_list_view, name='buy'),
    path('properties/rent/', rent_property_list_view, name='rent'),
    path('properties/commercial/', commercial_property_list_view, name='commercial'),
    path('properties/residential/', residential_property_list_view, name='residential'),
    path('properties/compare/', property_compare_view, name='compare'),
    path('search/', property_search_view, name='search'),
    path('properties/search/', property_search_view, name='search-alias'),
    path('post-property/', post_property_view, name='post-property'),
    path('properties/post-property/', post_property_view, name='post-property-alias'),
    path('properties/my-properties/', my_properties_view, name='my-properties'),
    path('property/<slug:slug>/', property_detail_view, name='detail'),
    path('properties/<slug:slug>/', property_detail_view, name='detail-properties'),
    path('property/<slug:slug>/edit/', edit_property_view, name='edit'),

    # Dynamic Property Form Field APIs
    path('api/property-fields', api_property_fields_list, name='api-property-fields'),
    path('api/admin/property-fields', api_admin_property_fields, name='api-admin-property-fields'),
    path('api/admin/property-fields/<int:pk>', api_admin_property_field_detail, name='api-admin-property-field-detail'),
    path('api/admin/property-fields/<int:pk>/status', api_admin_property_field_status, name='api-admin-property-field-status'),
    path('api/admin/property-fields/reorder', api_admin_property_fields_reorder, name='api-admin-property-fields-reorder'),
    path('api/admin/property-fields/<int:pk>/options', api_admin_property_field_options, name='api-admin-property-field-options'),
]
