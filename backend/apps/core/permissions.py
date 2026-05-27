from rest_framework.permissions import BasePermission


class IsOrganizationMember(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request, "current_organization", None) is not None


class IsOrganizationOwner(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        org = getattr(request, "current_organization", None)
        if org is None:
            return False
        role = getattr(request, "current_role", None)
        return role in ("owner", "admin")
