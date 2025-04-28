from django.db import models
from django.contrib.auth.models import User

class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    alert_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    public = models.BooleanField(default=False)
    dismissed_by = models.ManyToManyField(User, related_name="dismissed_alerts", blank=True)
    is_government = models.BooleanField(default=False)
    noaa_id = models.CharField(max_length=200, blank=True, null=True, unique=True)


    def __str__(self):
        return f"Alert for {self.city_name} ({self.zip_code})"
    def is_dismissed_for(self, user):
        return self.dismissed_by.filter(id=user.id).exists()
