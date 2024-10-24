from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as UserAdmin_

from app_admin.models import Token, User


@admin.register(User)
class UserAdmin(UserAdmin_):
    list_display = [
        "username",
        "email",
        "created_at",
        "is_staff",
        "is_active",
        "is_superuser",
    ]
    list_editable = ["is_staff", "is_active", "is_superuser"]
    list_filter = ["is_active", "is_staff"]
    search_fields = ["username", "email"]
    ordering = ["username"]
    fieldsets = (
        (None, {"fields": ("username", "email", "password", "last_login")}),
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


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ["key", "user__email"]
    list_select_related = ["user"]
    search_fields = ["key", "user__email"]
