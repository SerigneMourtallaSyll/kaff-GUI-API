from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.users.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):  # type: ignore[type-arg]
    list_display = ("email", "first_name", "last_name", "is_active", "is_staff", "created_at")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Identité"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        (_("Dates"), {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )

    readonly_fields = ("last_login",)
