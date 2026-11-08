from django.urls import path
from apps.locations.views import (
    api_states_list,
    api_districts_list,
    api_districts_by_state_id,
    api_cities_list,
    api_localities_list,
    api_sub_localities_list,
    api_location_search,
    api_location_hierarchy,
)

app_name = 'locations'

urlpatterns = [
    path('api/states/', api_states_list, name='api-states-direct'),
    path('api/districts/', api_districts_list, name='api-districts-direct'),
    path('api/districts/by-state/<str:state_id>/', api_districts_by_state_id, name='api-districts-by-state-direct'),
    path('api/locations/states/', api_states_list, name='api-states'),
    path('api/locations/districts/', api_districts_list, name='api-districts'),
    path('api/locations/districts/by-state/<str:state_id>/', api_districts_by_state_id, name='api-districts-by-state'),
    path('api/locations/cities/', api_cities_list, name='api-cities'),
    path('api/locations/localities/', api_localities_list, name='api-localities'),
    path('api/locations/sub-localities/', api_sub_localities_list, name='api-sub-localities'),
    path('api/locations/search/', api_location_search, name='api-search'),
    path('api/locations/hierarchy/', api_location_hierarchy, name='api-hierarchy'),
]
