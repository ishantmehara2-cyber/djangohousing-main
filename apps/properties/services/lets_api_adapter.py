import os
import logging
import json
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

class LetsApiAdapter:
    """
    Adapter service for integrating local property submissions with the external Let's API.
    Handles payload transformation, server-side authentication, timeouts, safe logging,
    and fallback handling so local property creation remains fail-safe.
    """

    @classmethod
    def is_enabled(cls):
        return os.getenv('LETS_API_ENABLED', 'True').lower() in ('true', '1', 't')

    @classmethod
    def get_api_url(cls):
        return os.getenv('LETS_API_URL', 'https://api.lets.co/v1/properties/sync').strip()

    @classmethod
    def get_api_key(cls):
        return os.getenv('LETS_API_KEY', '').strip()

    @classmethod
    def get_timeout(cls):
        try:
            return int(os.getenv('LETS_API_TIMEOUT', '10'))
        except ValueError:
            return 10

    @classmethod
    def build_payload(cls, property_obj):
        """
        Transforms internal Property model into Let's API expected JSON schema.
        """
        price_val = float(property_obj.price) if property_obj.price else (float(property_obj.rent) if property_obj.rent else 0.0)

        payload = {
            "external_id": str(property_obj.id),
            "idempotency_key": f"PROP-{property_obj.id}-{int(property_obj.created_at.timestamp()) if property_obj.created_at else 0}",
            "title": property_obj.title,
            "slug": property_obj.slug,
            "description": property_obj.description or "",
            "purpose": property_obj.listing_purpose,
            "category": property_obj.property_category,
            "property_type": property_obj.property_type.name if property_obj.property_type else "Residential",
            "pricing": {
                "amount": price_val,
                "currency": "INR",
                "rent": float(property_obj.rent) if property_obj.rent else None,
                "security_deposit": float(property_obj.security_deposit) if property_obj.security_deposit else None,
                "maintenance_fee": float(property_obj.maintenance_fee) if property_obj.maintenance_fee else None,
            },
            "specifications": {
                "bhk": property_obj.bhk,
                "bedrooms": property_obj.bedrooms,
                "bathrooms": property_obj.bathrooms,
                "balconies": property_obj.balconies,
                "carpet_area": float(property_obj.carpet_area) if property_obj.carpet_area else None,
                "area_unit": property_obj.area_unit,
                "furnishing": property_obj.furnishing,
                "floor_number": property_obj.floor_number,
                "total_floors": property_obj.total_floors,
            },
            "location": {
                "address": property_obj.address or "",
                "landmark": property_obj.landmark or "",
                "pincode": property_obj.pincode or "",
                "city": property_obj.city.name if property_obj.city else "",
                "locality": property_obj.locality.name if property_obj.locality else "",
                "latitude": float(property_obj.latitude) if property_obj.latitude else None,
                "longitude": float(property_obj.longitude) if property_obj.longitude else None,
            },
            "status": property_obj.listing_state,
            "posted_at": property_obj.created_at.isoformat() if property_obj.created_at else timezone.now().isoformat(),
        }
        return payload

    @classmethod
    def sync_property(cls, property_obj):
        """
        Sends property payload to Let's API with safe logging, timeout, and exception handling.
        Returns (success: bool, details: dict)
        """
        if not cls.is_enabled():
            logger.info(f"[Let's API] Integration disabled via LETS_API_ENABLED for Property ID {property_obj.id}")
            return False, {"message": "Integration disabled in configuration", "status": "SKIPPED"}

        api_url = cls.get_api_url()
        api_key = cls.get_api_key()

        if not api_key or api_key == 'your_lets_api_key_here':
            logger.warning(f"[Let's API] Missing LETS_API_KEY for Property ID {property_obj.id}. Skipping external dispatch.")
            return False, {"message": "LETS_API_KEY environment variable not configured", "status": "UNCONFIGURED"}

        payload = cls.build_payload(property_obj)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "HousingClone-LetsApiAdapter/1.0",
        }

        logger.info(f"[Let's API] Dispatching Property ID {property_obj.id} to {api_url}")

        max_attempts = 2
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                response = requests.post(
                    api_url,
                    json=payload,
                    headers=headers,
                    timeout=cls.get_timeout()
                )

                if response.status_code in (200, 201, 202):
                    logger.info(f"[Let's API] Successfully synced Property ID {property_obj.id}. Status: {response.status_code}")
                    try:
                        resp_data = response.json()
                    except Exception:
                        resp_data = {"raw_response": response.text}
                    return True, {"status": "SUCCESS", "status_code": response.status_code, "data": resp_data}

                elif response.status_code >= 500:
                    logger.warning(f"[Let's API] Server error {response.status_code} on attempt {attempt}/{max_attempts} for Property ID {property_obj.id}")
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                else:
                    logger.error(f"[Let's API] Client error {response.status_code} for Property ID {property_obj.id}: {response.text[:200]}")
                    return False, {"status": "FAILED", "status_code": response.status_code, "error": response.text[:300]}

            except requests.exceptions.Timeout:
                logger.warning(f"[Let's API] Timeout ({cls.get_timeout()}s) on attempt {attempt}/{max_attempts} for Property ID {property_obj.id}")
                last_error = "Request Timeout"
            except requests.exceptions.RequestException as e:
                logger.error(f"[Let's API] Network/Request error for Property ID {property_obj.id}: {str(e)}")
                last_error = str(e)
                break

        return False, {"status": "FAILED", "error": last_error or "Unknown error"}
