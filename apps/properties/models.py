from django.db import models
from django.conf import settings
from apps.locations.models import City, Locality, SubLocality
from apps.core.validators import validate_file_size_5mb, validate_image_file

class ListingPurposeChoices(models.TextChoices):
    BUY = 'BUY', 'Buy / Sale'
    RENT = 'RENT', 'Rent / Lease'
    COMMERCIAL = 'COMMERCIAL', 'Commercial'
    PG_COLIVING = 'PG_COLIVING', 'PG / Co-Living'
    PLOT = 'PLOT', 'Plot / Land'

class PropertyCategoryChoices(models.TextChoices):
    RESIDENTIAL = 'RESIDENTIAL', 'Residential'
    COMMERCIAL = 'COMMERCIAL', 'Commercial'
    AGRICULTURAL = 'AGRICULTURAL', 'Agricultural'
    INDUSTRIAL = 'INDUSTRIAL', 'Industrial'

class AreaUnitChoices(models.TextChoices):
    SQFT = 'SQFT', 'Sq. Ft.'
    SQYD = 'SQYD', 'Sq. Yd.'
    ACRE = 'ACRE', 'Acre'
    HECTARE = 'HECTARE', 'Hectare'

class FurnishingChoices(models.TextChoices):
    UNFURNISHED = 'UNFURNISHED', 'Unfurnished'
    SEMI_FURNISHED = 'SEMI_FURNISHED', 'Semi-Furnished'
    FULLY_FURNISHED = 'FULLY_FURNISHED', 'Fully Furnished'

class FacingChoices(models.TextChoices):
    EAST = 'EAST', 'East'
    WEST = 'WEST', 'West'
    NORTH = 'NORTH', 'North'
    SOUTH = 'SOUTH', 'South'
    NORTH_EAST = 'NORTH_EAST', 'North East'
    NORTH_WEST = 'NORTH_WEST', 'North West'
    SOUTH_EAST = 'SOUTH_EAST', 'South East'
    SOUTH_WEST = 'SOUTH_WEST', 'South West'

class PropertyAgeChoices(models.TextChoices):
    NEW_CONSTRUCTION = 'NEW_CONSTRUCTION', 'New Construction'
    LESS_THAN_1_YEAR = 'LESS_THAN_1_YEAR', 'Under 1 Year'
    ONE_TO_5_YEARS = 'ONE_TO_5_YEARS', '1 to 5 Years'
    FIVE_TO_10_YEARS = 'FIVE_TO_10_YEARS', '5 to 10 Years'
    TEN_PLUS_YEARS = 'TEN_PLUS_YEARS', '10+ Years'

class PossessionStatusChoices(models.TextChoices):
    READY_TO_MOVE = 'READY_TO_MOVE', 'Ready to Move'
    UNDER_CONSTRUCTION = 'UNDER_CONSTRUCTION', 'Under Construction'

class VerificationStateChoices(models.TextChoices):
    UNVERIFIED = 'UNVERIFIED', 'Unverified'
    PENDING = 'PENDING', 'Pending Verification'
    VERIFIED = 'VERIFIED', 'Verified'
    REJECTED = 'REJECTED', 'Rejected'

class ListingStateChoices(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
    ACTIVE = 'ACTIVE', 'Active'
    PAUSED = 'PAUSED', 'Paused'
    EXPIRED = 'EXPIRED', 'Expired'
    SOLD = 'SOLD', 'Sold'
    RENTED = 'RENTED', 'Rented'
    REJECTED = 'REJECTED', 'Rejected'

class MediaTypeChoices(models.TextChoices):
    IMAGE = 'IMAGE', 'Image'
    VIDEO = 'VIDEO', 'Video'
    FLOOR_PLAN = 'FLOOR_PLAN', 'Floor Plan'
    DOCUMENT_PDF = 'DOCUMENT_PDF', 'Document PDF'
    VIRTUAL_TOUR = 'VIRTUAL_TOUR', 'Virtual Tour'

class PropertyType(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=PropertyCategoryChoices.choices, default=PropertyCategoryChoices.RESIDENTIAL)
    icon = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'property_types'
        ordering = ['name']

    def __str__(self):
        return self.name

class Amenity(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    category = models.CharField(max_length=50, default='GENERAL')
    icon = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'amenities'
        verbose_name_plural = 'Amenities'
        ordering = ['name']

    def __str__(self):
        return self.name

class PropertyQuerySet(models.QuerySet):
    def public(self):
        """Returns only active, publicly viewable properties (excluding drafts, pending, sold, rented, etc.)."""
        return self.filter(listing_state=ListingStateChoices.ACTIVE).exclude(
            listing_state__in=[
                ListingStateChoices.DRAFT,
                ListingStateChoices.PENDING_APPROVAL,
                ListingStateChoices.REJECTED,
                ListingStateChoices.PAUSED,
                ListingStateChoices.EXPIRED,
                ListingStateChoices.SOLD,
                ListingStateChoices.RENTED,
            ]
        )

    def public_for_sale(self):
        return self.public().filter(
            models.Q(listing_purpose=ListingPurposeChoices.BUY) | models.Q(listing_purpose=ListingPurposeChoices.PLOT)
        ).exclude(listing_state=ListingStateChoices.SOLD)

    def public_for_rent(self):
        return self.public().filter(
            listing_purpose=ListingPurposeChoices.RENT
        ).exclude(listing_state=ListingStateChoices.RENTED)

    def public_commercial(self):
        return self.public().filter(
            models.Q(property_category=PropertyCategoryChoices.COMMERCIAL) | models.Q(listing_purpose=ListingPurposeChoices.COMMERCIAL)
        )

    def public_residential(self):
        return self.public().filter(
            property_category=PropertyCategoryChoices.RESIDENTIAL
        )

class Property(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    listing_purpose = models.CharField(max_length=20, choices=ListingPurposeChoices.choices, default=ListingPurposeChoices.BUY)
    property_category = models.CharField(max_length=20, choices=PropertyCategoryChoices.choices, default=PropertyCategoryChoices.RESIDENTIAL)
    property_type = models.ForeignKey(PropertyType, on_delete=models.RESTRICT, related_name='properties')

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_properties')
    posted_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_properties')
    assigned_agent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_properties')

    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    rent = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    security_deposit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    maintenance_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    bhk = models.IntegerField(null=True, blank=True)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.IntegerField(null=True, blank=True)
    balconies = models.IntegerField(null=True, blank=True)

    carpet_area = models.DecimalField(max_digits=10, decimal_places=2)
    built_up_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    area_unit = models.CharField(max_length=20, choices=AreaUnitChoices.choices, default=AreaUnitChoices.SQFT)

    furnishing = models.CharField(max_length=20, choices=FurnishingChoices.choices, default=FurnishingChoices.UNFURNISHED)
    floor_number = models.IntegerField(null=True, blank=True)
    total_floors = models.IntegerField(null=True, blank=True)
    facing = models.CharField(max_length=20, choices=FacingChoices.choices, null=True, blank=True)
    property_age = models.CharField(max_length=20, choices=PropertyAgeChoices.choices, null=True, blank=True)
    possession_status = models.CharField(max_length=20, choices=PossessionStatusChoices.choices, null=True, blank=True)
    possession_date = models.DateTimeField(null=True, blank=True)

    address = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    pincode = models.CharField(max_length=20, null=True, blank=True)

    state = models.ForeignKey('locations.State', on_delete=models.RESTRICT, null=True, blank=True, related_name='properties')
    district = models.ForeignKey('locations.District', on_delete=models.RESTRICT, null=True, blank=True, related_name='properties')
    city = models.ForeignKey(City, on_delete=models.RESTRICT, related_name='properties')
    locality = models.ForeignKey(Locality, on_delete=models.RESTRICT, related_name='properties')
    sub_locality = models.ForeignKey(SubLocality, on_delete=models.SET_NULL, null=True, blank=True, related_name='properties')

    latitude = models.FloatField(default=19.0760)
    longitude = models.FloatField(default=72.8777)

    verification_state = models.CharField(max_length=20, choices=VerificationStateChoices.choices, default=VerificationStateChoices.UNVERIFIED)
    listing_state = models.CharField(max_length=20, choices=ListingStateChoices.choices, default=ListingStateChoices.DRAFT)
    completed_step = models.IntegerField(default=1)
    views_count = models.IntegerField(default=0)
    rejection_reason = models.TextField(null=True, blank=True)

    # Main Property Thumbnail Reference
    thumbnail_media = models.ForeignKey('PropertyMedia', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    # Dynamic form field attributes store
    dynamic_attributes = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def get_main_thumbnail_url(self):
        """
        Returns the main selected property thumbnail file URL, falling back to first uploaded image if available.
        """
        if self.thumbnail_media and self.thumbnail_media.file:
            return self.thumbnail_media.file.url
        first_media = self.media.filter(media_type=MediaTypeChoices.IMAGE).first()
        if first_media and first_media.file:
            return first_media.file.url
        return '/static/images/placeholder-property.jpg'

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        if self.city_id and self.locality_id:
            if self.locality.city_id != self.city_id:
                raise ValidationError({"locality": "Selected locality does not belong to the selected city."})
        if self.city_id and self.district_id and self.city.district_id:
            if self.city.district_id != self.district_id:
                raise ValidationError({"district": "Selected district does not match the city's district."})
        if self.district_id and self.state_id:
            if self.district.state_id != self.state_id:
                raise ValidationError({"district": "Selected district does not belong to the selected state."})
        if self.city_id and self.state_id:
            if self.city.state_id != self.state_id:
                raise ValidationError({"city": "Selected city does not belong to the selected state."})

    def save(self, *args, **kwargs):
        if self.city_id:
            if not self.state_id:
                self.state_id = self.city.state_id
            if not self.district_id and self.city.district_id:
                self.district_id = self.city.district_id
        super().save(*args, **kwargs)

    objects = PropertyQuerySet.as_manager()

    class Meta:
        db_table = 'properties'
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['listing_state', 'listing_purpose', 'property_category']),
            models.Index(fields=['city', 'locality', 'listing_state']),
            models.Index(fields=['price', 'created_at']),
            models.Index(fields=['owner', 'listing_state']),
        ]

    def __str__(self):
        return self.title

class PropertyAmenity(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_amenities')
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name='amenity_properties')

    class Meta:
        db_table = 'property_amenities'
        unique_together = ('property', 'amenity')

class PropertyMedia(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='property_media/', validators=[validate_file_size_5mb])
    media_type = models.CharField(max_length=20, choices=MediaTypeChoices.choices, default=MediaTypeChoices.IMAGE)
    caption = models.CharField(max_length=255, null=True, blank=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'property_media'
        ordering = ['display_order', 'id']

class FieldTypeChoices(models.TextChoices):
    TEXT = 'text', 'Text'
    TEXTAREA = 'textarea', 'Textarea'
    NUMBER = 'number', 'Number'
    CURRENCY = 'currency', 'Currency'
    EMAIL = 'email', 'Email'
    PHONE = 'phone', 'Phone'
    SELECT = 'select', 'Single Select'
    MULTISELECT = 'multiselect', 'Multi-Select'
    CHECKBOX = 'checkbox', 'Checkbox'
    RADIO = 'radio', 'Radio Buttons'
    DATE = 'date', 'Date'
    YES_NO = 'yes_no', 'Yes/No'
    FILE = 'file', 'File Upload'

class PropertyFormField(models.Model):
    key = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=50, choices=FieldTypeChoices.choices, default=FieldTypeChoices.TEXT)
    required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    help_text = models.TextField(blank=True, null=True)

    applicable_categories = models.JSONField(default=list, blank=True) # e.g. ["RESIDENTIAL", "COMMERCIAL", "ALL"]
    applicable_listing_types = models.JSONField(default=list, blank=True) # e.g. ["BUY", "RENT", "ALL"]

    conditional_parent_key = models.CharField(max_length=100, blank=True, null=True)
    conditional_parent_value = models.CharField(max_length=100, blank=True, null=True)

    is_system_field = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'property_form_fields'
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.label} ({self.key})"

class PropertyFormFieldOption(models.Model):
    field = models.ForeignKey(PropertyFormField, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    class Meta:
        db_table = 'property_form_field_options'
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.label} ({self.value})"
