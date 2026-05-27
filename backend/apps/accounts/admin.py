from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Organization, OrganizationMember, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "name", "is_active", "is_staff"]
    search_fields = ["email", "name"]
    ordering = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Info", {"fields": ("name",)}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (None, {"fields": ("email", "name", "password1", "password2")}),
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "city", "state"]
    search_fields = ["name", "slug"]


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ["user", "organization", "role"]
