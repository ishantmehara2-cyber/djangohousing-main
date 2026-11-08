from django.db.models import Q
from apps.properties.models import Property, ListingPurposeChoices, PropertyCategoryChoices

class PropertySearchService:
    """
    Centralized advanced property search and filtering service using Django ORM.
    Handles location search, state, district, purpose, budget, BHK, property type,
    furnishing, area, availability, amenities, and keyword search with strict validation.
    """
    def __init__(self, query_params=None):
        self.query_params = query_params or {}

    def filter_properties(self):
        queryset = Property.objects.public().select_related(
            'state', 'district', 'city', 'locality', 'property_type', 'owner'
        ).prefetch_related(
            'media', 'property_amenities__amenity'
        )

        # 1. Purpose / Category Filter
        purpose = self.query_params.get('purpose') or self.query_params.get('listing_purpose')
        if purpose:
            purpose = purpose.upper()
            if purpose == 'BUY':
                queryset = queryset.filter(
                    Q(listing_purpose=ListingPurposeChoices.BUY) | Q(listing_purpose=ListingPurposeChoices.PLOT)
                ).exclude(listing_state='SOLD')
            elif purpose == 'RENT':
                queryset = queryset.filter(listing_purpose=ListingPurposeChoices.RENT).exclude(listing_state='RENTED')
            elif purpose == 'COMMERCIAL':
                queryset = queryset.filter(
                    Q(property_category=PropertyCategoryChoices.COMMERCIAL) | Q(listing_purpose=ListingPurposeChoices.COMMERCIAL)
                )
            else:
                queryset = queryset.filter(listing_purpose=purpose)

        # 2. State & District Location Filters
        state_param = self.query_params.get('state') or self.query_params.get('state_id')
        if state_param:
            if str(state_param).isdigit():
                queryset = queryset.filter(state_id=int(state_param))
            else:
                queryset = queryset.filter(Q(state__name__icontains=state_param) | Q(state__code__iexact=state_param))

        district_param = self.query_params.get('district') or self.query_params.get('district_id')
        if district_param:
            if str(district_param).isdigit():
                queryset = queryset.filter(district_id=int(district_param))
            else:
                queryset = queryset.filter(district__name__icontains=district_param)

        # 3. Location Search (City, Locality, Pincode)
        city = self.query_params.get('city')
        if city:
            queryset = queryset.filter(city__slug=city)

        locality = self.query_params.get('locality')
        if locality:
            queryset = queryset.filter(
                Q(locality__slug=locality) | Q(locality__name__icontains=locality) | Q(sub_locality__name__icontains=locality)
            )

        pincode = self.query_params.get('pincode')
        if pincode:
            queryset = queryset.filter(Q(pincode=pincode) | Q(locality__pincode=pincode))

        # 4. Keyword / Advanced Search (Title, Description, State, District, City, Locality, Type)
        keyword = self.query_params.get('keyword') or self.query_params.get('q')
        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(description__icontains=keyword) |
                Q(state__name__icontains=keyword) |
                Q(district__name__icontains=keyword) |
                Q(city__name__icontains=keyword) |
                Q(locality__name__icontains=keyword) |
                Q(property_type__name__icontains=keyword)
            )

        # 5. Budget Filters (Separating Buy Price vs Rent Price)
        min_price = self.query_params.get('min_price')
        max_price = self.query_params.get('max_price')

        is_rental = purpose == 'RENT'

        if min_price:
            try:
                min_val = float(min_price)
                if min_val >= 0:
                    if is_rental:
                        queryset = queryset.filter(rent__gte=min_val)
                    else:
                        queryset = queryset.filter(price__gte=min_val)
            except ValueError:
                pass

        if max_price:
            try:
                max_val = float(max_price)
                if max_val >= 0:
                    if is_rental:
                        queryset = queryset.filter(rent__lte=max_val)
                    else:
                        queryset = queryset.filter(price__lte=max_val)
            except ValueError:
                pass

        # 6. BHK Filter
        bhk_list = self.query_params.getlist('bhk') if hasattr(self.query_params, 'getlist') else []
        if not bhk_list and self.query_params.get('bhk'):
            bhk_val = self.query_params.get('bhk')
            bhk_list = [b.strip() for b in bhk_val.split(',') if b.strip()]

        if bhk_list:
            bhk_ints = []
            for b in bhk_list:
                try:
                    bhk_ints.append(int(b))
                except ValueError:
                    pass
            if bhk_ints:
                queryset = queryset.filter(bhk__in=bhk_ints)

        # 7. Property Type Filter
        prop_type = self.query_params.get('property_type')
        if prop_type:
            queryset = queryset.filter(property_type__slug=prop_type)

        # 8. Furnishing Filter
        furnishing = self.query_params.get('furnishing')
        if furnishing:
            queryset = queryset.filter(furnishing=furnishing)

        # 9. Area Filter (Carpet Area min / max)
        min_area = self.query_params.get('min_area')
        max_area = self.query_params.get('max_area')
        if min_area:
            try:
                queryset = queryset.filter(carpet_area__gte=float(min_area))
            except ValueError:
                pass
        if max_area:
            try:
                queryset = queryset.filter(carpet_area__lte=float(max_area))
            except ValueError:
                pass

        # 10. Property Availability / Possession Status Filter
        availability = self.query_params.get('availability') or self.query_params.get('possession_status')
        if availability:
            queryset = queryset.filter(possession_status=availability)

        # 11. Amenities Filter
        amenities = self.query_params.getlist('amenities') if hasattr(self.query_params, 'getlist') else []
        if not amenities and self.query_params.get('amenity'):
            amenities = [self.query_params.get('amenity')]

        for amenity_slug in amenities:
            if amenity_slug:
                queryset = queryset.filter(property_amenities__amenity__slug=amenity_slug)

        queryset = queryset.distinct()

        # 12. Sorting
        sort_param = self.query_params.get('sort', 'newest')
        sort_mapping = {
            'newest': '-created_at',
            'oldest': 'created_at',
            'price_low': 'price',
            'price_high': '-price',
            'updated': '-updated_at',
        }
        order_by_field = sort_mapping.get(sort_param, '-created_at')
        queryset = queryset.order_by(order_by_field)

        return queryset
