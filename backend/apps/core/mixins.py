from rest_framework.exceptions import PermissionDenied


class TenantScopedQuerySet:
    """Mixin para querysets que escopam por organization_id."""

    def for_organization(self, organization_id):
        return self.filter(organization_id=organization_id)


class TenantScopedViewSet:
    """
    Sobrescreve get_queryset() para filtrar sempre pelo organization_id
    do usuário autenticado na organização corrente.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        org = getattr(self.request, "current_organization", None)
        if org is None:
            raise PermissionDenied("Organização não definida na sessão.")
        return qs.filter(organization_id=org.id)

    def perform_create(self, serializer):
        org = getattr(self.request, "current_organization", None)
        if org is None:
            raise PermissionDenied("Organização não definida na sessão.")
        serializer.save(organization=org, organization_id=org.id)
