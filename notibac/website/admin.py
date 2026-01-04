from django.contrib import admin

from .models import PhoneNumber


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "user", "is_primary", "is_verified", "created_at")
    list_filter = ("is_primary", "is_verified")
    search_fields = ("phone_number", "user__email")
