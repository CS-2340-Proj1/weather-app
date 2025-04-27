from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import FavoriteZip              # or whatever you named it
from accounts.models import BirthCitySecret  # security answer


# ----------  inlines  ---------- #
class FavoriteZipInline(admin.TabularInline):
    model = FavoriteZip
    extra = 1            # show one blank row for quick add
    fields = ('zip_code',)
    # optional: make the ZIP column searchable inside the inline
    # autocomplete_fields = ('zip_code',)


class BirthCityInline(admin.StackedInline):
    model = BirthCitySecret
    extra = 0            # only one row allowed
    can_delete = False


# ----------  extend Django's User admin  ---------- #
class UserAdmin(BaseUserAdmin):
    inlines = (BirthCityInline, FavoriteZipInline)


# ----------  register  ---------- #
# First unregister the original User admin
admin.site.unregister(User)
# Then register our extended version
admin.site.register(User, UserAdmin)

# Also expose FavoriteZip in list view if you want to browse them directly
@admin.register(FavoriteZip)
class FavoriteZipAdmin(admin.ModelAdmin):
    list_display = ('user', 'zip_code')
    search_fields = ('zip_code', 'user__username')
