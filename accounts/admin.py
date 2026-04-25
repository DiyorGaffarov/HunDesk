from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "department", "is_active")
    list_filter = ("role", "department", "is_active")
    search_fields = ("username", "full_name", "email")
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Extra Profile Info",
            {
                "fields": (
                    "full_name",
                    "phone_number",
                    "role",
                    "department",
                    "profile_photo",
                )
            },
        ),
    )

# Register your models here.
