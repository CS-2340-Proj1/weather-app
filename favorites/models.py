from django.db import models
from django.contrib.auth.models import User


class FavoriteZip(models.Model):
    """Stores one ZIP code per user; duplicates not allowed."""
    user      = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='favorite_zips')
    zip_code  = models.CharField(max_length=15)
    city_name = models.CharField(
        max_length=120,
        default='',  # <─ satisfies existing rows
        blank=True  # allows empty string in admin/forms
    )
    class Meta:
        unique_together = ('user', 'zip_code')
        ordering = ['city_name']

    def __str__(self):
        return f'{self.zip_code} – {self.user}'