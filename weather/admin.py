from django.contrib import admin
from .models import Alert

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('city_name', 'zip_code', 'user', 'public')
    list_filter = ('public', 'zip_code')
    search_fields = ('city_name', 'zip_code', 'alert_text')