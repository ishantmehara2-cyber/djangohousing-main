from django import forms
from apps.properties.models import ListingPurposeChoices, FurnishingChoices, PossessionStatusChoices, PropertyType, Amenity
from apps.locations.models import City

class PropertySearchForm(forms.Form):
    keyword = forms.CharField(required=False, max_length=100)
    city = forms.CharField(required=False, max_length=50)
    locality = forms.CharField(required=False, max_length=100)
    purpose = forms.ChoiceField(required=False, choices=[('', 'All Purposes')] + list(ListingPurposeChoices.choices))
    property_type = forms.CharField(required=False, max_length=50)
    min_price = forms.DecimalField(required=False, max_digits=14, decimal_places=2, min_value=0)
    max_price = forms.DecimalField(required=False, max_digits=14, decimal_places=2, min_value=0)
    bhk = forms.CharField(required=False, max_length=20)
    furnishing = forms.ChoiceField(required=False, choices=[('', 'Any Furnishing')] + list(FurnishingChoices.choices))
    min_area = forms.DecimalField(required=False, max_digits=10, decimal_places=2, min_value=0)
    max_area = forms.DecimalField(required=False, max_digits=10, decimal_places=2, min_value=0)
    availability = forms.ChoiceField(required=False, choices=[('', 'Any Availability')] + list(PossessionStatusChoices.choices))
    sort = forms.CharField(required=False, max_length=30, initial='newest')

    def clean(self):
        cleaned_data = super().clean()
        min_p = cleaned_data.get('min_price')
        max_p = cleaned_data.get('max_price')
        if min_p is not None and max_p is not None and min_p > max_p:
            raise forms.ValidationError("Minimum price cannot exceed maximum price.")

        min_a = cleaned_data.get('min_area')
        max_a = cleaned_data.get('max_area')
        if min_a is not None and max_a is not None and min_a > max_a:
            raise forms.ValidationError("Minimum area cannot exceed maximum area.")

        return cleaned_data
