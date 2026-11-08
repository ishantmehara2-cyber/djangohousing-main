from django.db import models

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, default='India')
    iso_code = models.CharField(max_length=10, unique=True, default='IN')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'countries'
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name

class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states', null=True, blank=True)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    state_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    lgd_code = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.state_code and not self.code:
            self.code = self.state_code
        elif self.code and not self.state_code:
            self.state_code = self.code
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'states'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code or self.state_code})"

class District(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=150)
    lgd_code = models.CharField(max_length=20, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'districts'
        ordering = ['name']
        unique_together = ('state', 'name')
        indexes = [
            models.Index(fields=['state', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name}, {self.state.name}"

class City(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='cities')
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='cities', null=True, blank=True)
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    lgd_code = models.CharField(max_length=20, null=True, blank=True)
    city_type = models.CharField(max_length=50, default='City')
    latitude = models.FloatField(default=19.0760)
    longitude = models.FloatField(default=72.8777)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'cities'
        ordering = ['-is_popular', 'name']
        verbose_name_plural = 'Cities'
        indexes = [
            models.Index(fields=['state', 'district', 'is_active']),
            models.Index(fields=['is_popular', 'is_active']),
        ]

    def __str__(self):
        dist_name = f", {self.district.name}" if self.district else ""
        return f"{self.name}{dist_name}, {self.state.code or self.state.state_code}"

class Locality(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='localities')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    pincode = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.FloatField(default=19.0760)
    longitude = models.FloatField(default=72.8777)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'localities'
        ordering = ['name']
        unique_together = ('city', 'slug')
        verbose_name_plural = 'Localities'
        indexes = [
            models.Index(fields=['city', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name}, {self.city.name}"

class SubLocality(models.Model):
    locality = models.ForeignKey(Locality, on_delete=models.CASCADE, related_name='sub_localities')
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150)
    pincode = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.FloatField(default=19.0760)
    longitude = models.FloatField(default=72.8777)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'sub_localities'
        ordering = ['name']
        unique_together = ('locality', 'slug')
        verbose_name_plural = 'Sub Localities'
        indexes = [
            models.Index(fields=['locality', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name}, {self.locality.name}"
