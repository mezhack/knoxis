from .models import OrganizationMember


class CurrentOrganizationMiddleware:
    """
    Resolve a organização atual do usuário autenticado a partir da sessão.
    Injeta request.current_organization e request.current_role.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.current_organization = None
        request.current_role = None

        if request.user and request.user.is_authenticated:
            org_id = request.session.get("current_organization_id")
            if org_id:
                try:
                    membership = OrganizationMember.objects.select_related("organization").get(
                        user=request.user, organization_id=org_id
                    )
                    request.current_organization = membership.organization
                    request.current_role = membership.role
                except OrganizationMember.DoesNotExist:
                    pass

            if request.current_organization is None:
                membership = (
                    OrganizationMember.objects.filter(user=request.user)
                    .select_related("organization")
                    .first()
                )
                if membership:
                    request.current_organization = membership.organization
                    request.current_role = membership.role
                    request.session["current_organization_id"] = membership.organization_id

        return self.get_response(request)
