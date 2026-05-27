import structlog
from axes.decorators import axes_dispatch
from django.conf import settings
from django.contrib.auth import login, logout
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import AuditLog, get_client_ip

from .models import OrganizationMember
from .serializers import (
    LoginSerializer,
    OrganizationSerializer,
    SignupSerializer,
    UserSerializer,
)

logger = structlog.get_logger()


def axes_lockout_response(request, credentials, *args, **kwargs):
    return JsonResponse(
        {
            "type": "rate_limit",
            "title": "Muitas tentativas",
            "status": 429,
            "detail": "Muitas tentativas de login. Tente novamente em 30 minutos.",
        },
        status=429,
    )


class SignupView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            serializer = SignupSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {
                        "type": "validation_error",
                        "title": "Dados inválidos",
                        "status": 400,
                        "fields": serializer.errors,
                    },
                    status=400,
                )
            user, org = serializer.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            logger.info("user.signup", user_id=user.id, org_id=org.id)
            try:
                AuditLog.objects.create(
                    organization=org,
                    user=user,
                    action="account.signup",
                    target_type="organization",
                    target_id=org.id,
                    ip_address=get_client_ip(request),
                )
            except Exception as audit_exc:
                logger.error("audit_log.signup.failed", error=str(audit_exc))
            return Response(
                {
                    "user": UserSerializer(user).data,
                    "organization": OrganizationSerializer(org).data,
                },
                status=201,
            )
        except Exception as exc:
            logger.error("signup.error", error=str(exc), exc_info=True)
            detail = str(exc) if settings.DEBUG else "Erro interno do servidor."
            return Response(
                {"type": "server_error", "title": "Erro interno", "status": 500, "detail": detail},
                status=500,
            )


@method_decorator(axes_dispatch, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            logger.warning("user.login.failed", email=request.data.get("email", ""))
            return Response(
                {
                    "type": "validation_error",
                    "title": "Dados inválidos",
                    "status": 400,
                    "fields": serializer.errors,
                },
                status=400,
            )
        user = serializer.validated_data["user"]
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        memberships = OrganizationMember.objects.filter(user=user).select_related("organization")
        organizations = [
            {"id": m.organization.id, "name": m.organization.name, "slug": m.organization.slug, "role": m.role}
            for m in memberships
        ]
        logger.info("user.login", user_id=user.id)
        AuditLog.objects.create(
            user=user,
            action="account.login",
            ip_address=get_client_ip(request),
        )
        return Response({"user": UserSerializer(user).data, "organizations": organizations})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info("user.logout", user_id=request.user.id)
        logout(request)
        return Response(status=204)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        org = getattr(request, "current_organization", None)
        role = getattr(request, "current_role", None)

        if org is None:
            memberships = OrganizationMember.objects.filter(user=request.user).select_related("organization")
            if memberships.exists():
                m = memberships.first()
                org = m.organization
                role = m.role
                request.session["current_organization_id"] = org.id

        return Response(
            {
                "user": UserSerializer(request.user).data,
                "current_organization": OrganizationSerializer(org).data if org else None,
                "role": role,
            }
        )
