from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as UserAdmin_

from app_admin.models import User


@admin.register(User)
class UserAdmin(UserAdmin_):
    list_display = [
        "email",
        "created_at",
        "is_staff",
        "is_active",
    ]
    list_editable = ["is_staff", "is_active"]
    list_filter = ["is_active", "is_staff"]
    search_fields = ["email"]
    ordering = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password", "last_login")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2"),
            },
        ),
    )
