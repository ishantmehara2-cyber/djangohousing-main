from apps.properties.services.search import PropertySearchService

def apply_property_filters(request_data):
    """
    Wrapper function utilizing PropertySearchService to filter properties based on request GET data.
    """
    search_service = PropertySearchService(query_params=request_data)
    return search_service.filter_properties()
