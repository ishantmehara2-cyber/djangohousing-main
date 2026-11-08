from django.db.models import Q
from apps.properties.models import Property, ListingStateChoices
from apps.engagements.models import UserPreference, RecentlyViewed, Favorite

class PropertyRecommendationService:
    """
    Transparent weighted rule-based property recommendation engine.
    Calculates preference match scores and provides user-understandable recommendation reasons.
    """
    @classmethod
    def get_recommendations_for_user(cls, user, limit=6):
        if not user or not user.is_authenticated:
            properties = list(Property.objects.public().select_related('city', 'locality', 'property_type')[:limit])
            for p in properties:
                p.recommendation_reason = "Popular verified listing across India"
            return properties

        pref = UserPreference.objects.filter(user=user).select_related('city', 'locality', 'property_type').first()
        base_qs = Property.objects.public().exclude(owner=user).select_related('city', 'locality', 'property_type').prefetch_related('media')

        if pref and pref.purpose:
            base_qs = base_qs.filter(listing_purpose=pref.purpose)

        candidates = list(base_qs[:50])
        scored_properties = []

        for prop in candidates:
            score = 0
            reasons = []

            if pref:
                if pref.purpose and prop.listing_purpose == pref.purpose:
                    score += 20
                    reasons.append(f"Matches your preference for {prop.get_listing_purpose_display()}")

                if pref.city and prop.city_id == pref.city_id:
                    score += 15
                    reasons.append(f"Located in your preferred city ({prop.city.name})")
                    if pref.locality and prop.locality_id == pref.locality_id:
                        score += 10
                        reasons.append(f"Located in {prop.locality.name}")

                prop_price = prop.rent if prop.listing_purpose == 'RENT' else prop.price
                if prop_price is not None:
                    if pref.min_price and prop_price >= pref.min_price:
                        score += 10
                    if pref.max_price and prop_price <= pref.max_price:
                        score += 10
                        if not reasons or len(reasons) < 2:
                            reasons.append("Fits your budget range")

                if pref.property_type and prop.property_type_id == pref.property_type_id:
                    score += 10
                    reasons.append(f"Matches type {prop.property_type.name}")

                if prop.bhk and pref.min_bhk and pref.max_bhk:
                    if pref.min_bhk <= prop.bhk <= pref.max_bhk:
                        score += 10
                        reasons.append(f"{prop.bhk} BHK configuration")

                if pref.furnishing and prop.furnishing == pref.furnishing:
                    score += 5

            prop.score = score
            prop.recommendation_reason = ". ".join(reasons) if reasons else "Matches your activity and preferred specifications"
            scored_properties.append(prop)

        scored_properties.sort(key=lambda x: getattr(x, 'score', 0), reverse=True)
        return scored_properties[:limit]

    @classmethod
    def get_recommendations(cls, user, limit=6):
        return cls.get_recommendations_for_user(user, limit)

    @classmethod
    def get_similar_properties(cls, property_item, limit=4):
        qs = Property.objects.public().filter(
            city=property_item.city,
            listing_purpose=property_item.listing_purpose
        ).exclude(id=property_item.id).select_related('city', 'locality', 'property_type')

        locality_qs = list(qs.filter(locality=property_item.locality)[:limit])
        if len(locality_qs) < limit:
            remaining_limit = limit - len(locality_qs)
            other_qs = list(qs.exclude(locality=property_item.locality)[:remaining_limit])
            locality_qs.extend(other_qs)

        return locality_qs
