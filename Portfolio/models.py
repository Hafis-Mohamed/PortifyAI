from django.db import models
from django.contrib.auth.models import User

class Resume(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    resume=models.FileField(upload_to="resumes/")
    uploaded_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.uploaded_at:%Y-%m-%d %H:%M}"   

class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    
    # Basic info
    name = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    other_links = models.TextField(blank=True, null=True)
    
    # JSON Fields for arrays
    education = models.JSONField(default=list, blank=True)
    experience = models.JSONField(default=list, blank=True)
    projects = models.JSONField(default=list, blank=True)
    certifications = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    languages = models.JSONField(default=list, blank=True) # Will store list of dicts: {"name": "English", "proficiency": "Native"}
    interests = models.JSONField(default=list, blank=True)
    achievements = models.JSONField(default=list, blank=True)
    publications = models.JSONField(default=list, blank=True)
    volunteer = models.JSONField(default=list, blank=True)
    
    # Template Selection
    template_choice = models.CharField(max_length=50, blank=True, null=True, default='template1')
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Portfolio of {self.user.username}"


class PortfolioURL(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio_url')
    url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Portfolio URL of {self.user.username}"