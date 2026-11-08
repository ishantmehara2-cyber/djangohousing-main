from django.db import models
from django.conf import settings
from apps.locations.models import City, Locality
from apps.properties.models import VerificationStateChoices, MediaTypeChoices

class DeveloperOrganization(models.Model):
    company_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    logo = models.ImageField(upload_to='developer_logos/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    established_year = models.IntegerField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=VerificationStateChoices.choices, default=VerificationStateChoices.UNVERIFIED)

    class Meta:
        db_table = 'developer_organizations'

    def __str__(self):
        return self.company_name

class DeveloperMember(models.Model):
    organization = models.ForeignKey(DeveloperOrganization, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='developer_memberships')
    role_title = models.CharField(max_length=100, default='Associate')

    class Meta:
        db_table = 'developer_members'

class Project(models.Model):
    developer = models.ForeignKey(DeveloperOrganization, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    city = models.ForeignKey(City, on_delete=models.RESTRICT, related_name='projects')
    locality = models.ForeignKey(Locality, on_delete=models.RESTRICT, related_name='projects')
    rera_id = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'projects'

    def __str__(self):
        return self.name

class ProjectMedia(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='project_media/')
    media_type = models.CharField(max_length=20, choices=MediaTypeChoices.choices, default=MediaTypeChoices.IMAGE)

    class Meta:
        db_table = 'project_media'
